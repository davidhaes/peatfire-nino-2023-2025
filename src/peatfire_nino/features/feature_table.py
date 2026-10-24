"""feature_table.py
Assemble the cell-month feature table with binary fire labels.
Weather enters for the same month; surface state (NDWI, LST, soil moisture)
enters from the previous month only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from peatfire_nino.config import DRY_SEASON_MONTHS, STUDY_YEARS
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


def _fire_labels(year: int) -> pd.DataFrame:
    fires = fetch_firms(year)
    labels = fires[["cell_id", "month", "n_fire_px", "n_fire_days_px"]].copy()
    labels["fire"] = (labels["n_fire_px"] > 0).astype(int)
    return labels


def build_feature_table() -> pd.DataFrame:
    """One row per cell and dry-season month.

    Weather (VPD, wind, precipitation, temperature) enters for the same month:
    it is exogenous to the fire. Surface state (NDWI, LST, soil moisture)
    enters only from the previous month. Same-month NDWI and LST respond to
    the fire itself through burn scars, smoke and heat, which made NDWI the
    "strongest driver" in the earlier version for partly the wrong reason.
    """
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

        monthly = (clim[["cell_id", "month", "vpd", "wind_speed", "precip_mm", "t2m_c"]]
                   .merge(dyn[["cell_id", "month", "ndwi", "lst_k", "soil_moisture"]],
                          on=["cell_id", "month"], how="left")
                   .sort_values(["cell_id", "month"]))
        grp = monthly.groupby("cell_id")
        # Previous month, including May for the June row.
        for col, lag in (("vpd", "vpd_lag1"), ("precip_mm", "precip_lag1"),
                         ("soil_moisture", "sm_lag1"), ("ndwi", "ndwi_lag1"), ("lst_k", "lst_lag1")):
            monthly[lag] = grp[col].shift(1)
        monthly["precip_cum2"] = monthly["precip_mm"] + monthly["precip_lag1"]
        monthly = monthly[monthly["month"].isin(DRY_SEASON_MONTHS)]

        labels = _fire_labels(year)
        df = (monthly.merge(grid_attr, on="cell_id", how="left")
              .merge(ft, on="cell_id", how="left")
              .merge(peat, on="cell_id", how="left")
              .merge(labels, on=["cell_id", "month"], how="left"))
        df["fire"] = df["fire"].fillna(0).astype(int)
        df["n_fire_px"] = df["n_fire_px"].fillna(0.0)
        df["n_fire_days_px"] = df["n_fire_days_px"].fillna(0.0)
        df["year"] = year
        frames.append(df)

    table = pd.concat(frames, ignore_index=True)
    for col in ("peat_likely",):
        table[col] = table[col].fillna(0).astype(int)
    for col in ("peat_share", "peat_thickness_cm"):
        table[col] = table[col].fillna(0.0)

    # Missing surface-state values stay missing; LightGBM handles them and a
    # median fill would hide how often a cell was clouded out.
    table = table.dropna(subset=["vpd", "elevation"])
    table = table.sort_values(["year", "cell_id", "month"]).reset_index(drop=True)

    table.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "Multi-modal fire feature table (cell-month-year, dynamic+lag)",
        "source": "Derived: FIRMS (MODIS) + ERA5-Land + Hansen + MERIT + PEATGRIDS + MODIS/SMAP",
        "source_url": "see individual raw metadata",
        "license": "Derived product",
        "access_date": pd.Timestamp.today().date().isoformat(),
        "spatial_resolution": "3 km grid, monthly",
        "temporal_coverage": f"{STUDY_YEARS[0]}-{STUDY_YEARS[-1]} dry season, monthly",
        "preprocessing_steps": "join static fuel/terrain + PEATGRIDS peat + same-month ERA5 weather + "
                               "previous-month NDWI/LST/SM and weather lags + MODIS fire-pixel labels",
        "unit": "vpd kPa; wind m/s; precip mm/day; ndwi [-1,1]; lst K; sm m3/m3; fire 0/1; n_fire_px count",
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
