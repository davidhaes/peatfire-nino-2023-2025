"""era5.py
ERA5-Land monthly predictors via GEE: temperature, dewpoint, precip, 10m winds.
Reduced to the analysis grid per month (batched to respect GEE limits).
"""
from __future__ import annotations

import calendar
from datetime import date

import ee
import geopandas as gpd
import pandas as pd
from tqdm import tqdm

from peatfire_nino.config import PREDICTOR_MONTHS, GEE_ASSETS
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW

_BANDS = {
    "temperature_2m": "t2m_k",
    "dewpoint_temperature_2m": "td2m_k",
    "total_precipitation_sum": "precip_m",
    "u_component_of_wind_10m": "u10",
    "v_component_of_wind_10m": "v10",
}


def fetch_era5_predictors(year: int) -> pd.DataFrame:
    """Per-cell, per-month ERA5-Land predictors for `year`, cached parquet."""
    out = DATA_RAW / f"era5_predictors_{year}.parquet"
    if file_exists(out, f"ERA5 predictors {year}"):
        return pd.read_parquet(out)

    init_earth_engine()
    grid = build_grid(load_districts())

    grid_cent = grid.to_crs(3857).copy()
    grid_cent["geometry"] = grid_cent.geometry.centroid
    grid_cent = grid_cent.to_crs(4326)
    cell_ids = grid_cent["cell_id"].tolist()

    BATCH = 2000
    recs = []
    for m in tqdm(PREDICTOR_MONTHS, desc=f"ERA5 {year} months"):
        start = ee.Date.fromYMD(year, m, 1)
        end = start.advance(1, "month")  # exclusive, keeps the last day
        coll = (ee.ImageCollection(GEE_ASSETS["era5_land_daily"])
                .filterDate(start, end)
                .select(list(_BANDS.keys())))
        composite = coll.mean().rename(list(_BANDS.values()))

        for i in range(0, len(cell_ids), BATCH):
            batch_ids = cell_ids[i:i + BATCH]
            sub = grid_cent[grid_cent["cell_id"].isin(batch_ids)]
            feats = [
                ee.Feature(ee.Geometry.Point([r.geometry.x, r.geometry.y]),
                           {"cell_id": int(r["cell_id"])})
                for _, r in sub.iterrows()
            ]
            fc_batch = ee.FeatureCollection(feats)
            reduced = composite.reduceRegions(
                collection=fc_batch, reducer=ee.Reducer.mean(), scale=1000)
            for f in reduced.getInfo()["features"]:
                p = f["properties"]
                recs.append({
                    "cell_id": int(p["cell_id"]),
                    "month": m,
                    "t2m_k": p.get("t2m_k"),
                    "td2m_k": p.get("td2m_k"),
                    "precip_m": p.get("precip_m"),
                    "u10": p.get("u10"),
                    "v10": p.get("v10"),
                    "year": year,
                })

    df = pd.DataFrame(recs).dropna(subset=["t2m_k", "td2m_k"])

    df.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "ERA5-Land daily aggregated (monthly mean per cell)",
        "source": "ECMWF Copernicus C3S via Google Earth Engine",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/"
                      "ECMWF_ERA5_LAND_DAILY_AGGR",
        "license": "Copernicus C3S license (free, attribution required)",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "~9 km native, reduced to grid cells",
        "temporal_coverage": f"{year} May-Nov, monthly means",
        "preprocessing_steps": "per month: ImageCollection.mean, batched reduceRegions to grid",
        "unit": "t2m/td2m in K; precip in m; winds in m/s",
        "citation_apa": "Munoz-Sabater, J., et al. (2021). ERA5-Land: a state-of-the-art global "
                        "reanalysis dataset for land applications. Earth System Science Data, "
                        "13(9), 4349-4383.",
        "citation_bibtex": "@article{munoz2021era5land,title={ERA5-Land: a state-of-the-art "
                           "global reanalysis dataset for land applications},author={Mu{\~n}oz-"
                           "Sabater, J. and others},journal={Earth System Science Data},"
                           "volume={13},number={9},pages={4349--4383},year={2021}}",
        "crs": "EPSG:4326",
    })
    log_step(f"ERA5 {year}: {len(df)} cell-month predictor rows", "OK")
    return df
