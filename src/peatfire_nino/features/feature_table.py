"""feature_table.py
Assemble pixel-month feature table with binary fire labels per cell-month-year.
Includes dynamic predictors (NDWI, LST, soil moisture) and temporal lag features.
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from peatfire_nino.config import STUDY_YEARS
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.data.era5 import fetch_era5_predictors
from peatfire_nino.data.fuel_terrain import fetch_fuel_terrain
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.data.peat import fetch_peat_extent
from peatfire_nino.data.dynamic import fetch_dynamic_predictors
from peatfire_nino.features.vpd import vpd_kpa
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_PROCESSED


def _fire_labels(grid: gpd.GeoDataFrame, year: int) -> pd.DataFrame:
    fires = fetch_firms(year)
    joined = gpd.sjoin(fires, grid[["cell_id", "geometry"]], predicate="within", how="inner")
    agg = (joined.groupby(["cell_id", "month"])
           .agg(frp_sum=("frp", "sum"), n_det=("frp", "size"))
           .reset_index())
    agg["fire"] = 1
    return agg


def build_feature_table() -> pd.DataFrame:
    out = DATA_PROCESSED / "feature_table.parquet"
    if out.exists():
        log_step(f"Using cached file {out.name}", "INFO")
        return pd.read_parquet(out)

    grid = build_grid(load_districts())
    ft = fetch_fuel_terrain()
    peat = fetch_peat_extent()
    grid_attr = grid[["cell_id", "district"]].drop_duplicates("cell_id")

    frames = []
    for year in STUDY_YEARS:
        clim = fetch_era5_predictors(year).copy()
        clim["t2m_c"] = clim["t2m_k"] - 273.15
        clim["td2m_c"] = clim["td2m_k"] - 273.15
        clim["vpd"] = vpd_kpa(clim["t2m_c"].to_numpy(), clim["td2m_c"].to_numpy())
        clim["wind_speed"] = np.sqrt(clim["u10"] ** 2 + clim["v10"] ** 2)
        clim["precip_mm"] = clim["precip_m"] * 1000.0

        dyn = fetch_dynamic_predictors(year)
        labels = _fire_labels(grid, year)

        df = (clim[["cell_id", "month", "vpd", "wind_speed", "precip_mm", "t2m_c"]]
              .merge(grid_attr, on="cell_id", how="left")
              .merge(ft, on="cell_id", how="left")
              .merge(peat, on="cell_id", how="left")
              .merge(dyn[["cell_id", "month", "ndwi", "lst_k", "soil_moisture"]],
                     on=["cell_id", "month"], how="left")
              .merge(labels[["cell_id", "month", "fire", "frp_sum", "n_det"]],
                     on=["cell_id", "month"], how="left"))
        df["fire"] = df["fire"].fillna(0).astype(int)
        df["frp_sum"] = df["frp_sum"].fillna(0.0)
        df["n_det"] = df["n_det"].fillna(0).astype(int)
        df["year"] = year
        frames.append(df)

    table = pd.concat(frames, ignore_index=True)
    table["peat_likely"] = table["peat_likely"].fillna(0).astype(int)

    # --- A2: temporal lag features (per cell, per year, ordered by month) ---
    table = table.sort_values(["year", "cell_id", "month"]).reset_index(drop=True)
    grp = table.groupby(["year", "cell_id"])
    table["vpd_lag1"] = grp["vpd"].shift(1)
    table["precip_lag1"] = grp["precip_mm"].shift(1)
    table["sm_lag1"] = grp["soil_moisture"].shift(1)
    # rolling 2-month cumulative precip (current + previous)
    table["precip_cum2"] = grp["precip_mm"].transform(
        lambda s: s.rolling(2, min_periods=1).sum())

    # fill NaNs: dynamic predictors with column median; lags with current-month value
    for col in ["ndwi", "lst_k", "soil_moisture"]:
        table[col] = table[col].fillna(table[col].median())
    table["vpd_lag1"] = table["vpd_lag1"].fillna(table["vpd"])
    table["precip_lag1"] = table["precip_lag1"].fillna(table["precip_mm"])
    table["sm_lag1"] = table["sm_lag1"].fillna(table["soil_moisture"])

    table = table.dropna(subset=["vpd", "elevation"])

    table.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "Multi-modal fire feature table (cell-month-year, dynamic+lag)",
        "source": "Derived: FIRMS + ERA5 + Hansen + MERIT + peat + MODIS/SMAP dynamic",
        "source_url": "see individual raw metadata",
        "license": "Derived product",
        "access_date": pd.Timestamp.today().date().isoformat(),
        "spatial_resolution": "3 km grid, monthly",
        "temporal_coverage": f"{STUDY_YEARS[0]}-{STUDY_YEARS[-1]} dry season, monthly",
        "preprocessing_steps": "join static + monthly climate + dynamic (NDWI/LST/SM) + "
                               "lag features (t-1 VPD/precip/SM, 2-month cum precip) + fire labels",
        "unit": "vpd kPa; wind m/s; precip mm; ndwi [-1,1]; lst K; sm m3/m3; fire 0/1",
        "citation_apa": "Field, R. D., et al. (2016). Indonesian fire activity and smoke "
                        "pollution in 2015. PNAS, 113(33), 9204-9209.",
        "citation_bibtex": "@article{field2016indonesian,title={Indonesian fire activity...},"
                           "author={Field, R. D. and others},journal={PNAS},volume={113},"
                           "number={33},pages={9204--9209},year={2016}}",
        "crs": "EPSG:4326",
    })
    log_step(f"feature table: {len(table)} cell-month rows, "
             f"{int(table['fire'].sum())} fire-positive, {table.shape[1]} cols", "OK")
    return table
