"""dynamic.py
Monthly dynamic predictors from GEE: NDWI, soil moisture, land surface temperature.
These vary month-to-month, unlike static fuel/terrain, to improve model skill.

Two corrections from the September 2026 audit:

* MOD09A1 is now masked with its StateQA band (cloud, cloud shadow, high
  aerosol, internal cloud and internal fire flags). Unmasked monthly means
  mixed cloud and smoke into NDWI, and in a fire month the smoke comes from
  the fire being predicted.
* A month with no usable image is stored as missing, not as zero. The
  earlier fallback wrote NDWI 0, LST 0 K and soil moisture 0 into the table.

The model uses these variables from the previous month only (see
features/feature_table.py), so the May values are fetched as well.
"""
from __future__ import annotations

import calendar
from datetime import date

import ee
import pandas as pd
from tqdm import tqdm

from peatfire_nino.config import PREDICTOR_MONTHS
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW


def _mask_mod09(image: ee.Image) -> ee.Image:
    """Keep clear, shadow-free, low-aerosol, non-fire MOD09A1 pixels."""
    qa = image.select("StateQA")
    clear = qa.bitwiseAnd(3).eq(0)                         # bits 0-1 cloud state
    no_shadow = qa.bitwiseAnd(1 << 2).eq(0)                # bit 2 cloud shadow
    not_high_aerosol = qa.rightShift(6).bitwiseAnd(3).neq(3)  # bits 6-7 aerosol quantity
    no_internal_cloud = qa.bitwiseAnd(1 << 10).eq(0)       # bit 10
    no_internal_fire = qa.bitwiseAnd(1 << 11).eq(0)        # bit 11
    keep = clear.And(no_shadow).And(not_high_aerosol).And(no_internal_cloud).And(no_internal_fire)
    return image.select(["sur_refl_b02", "sur_refl_b06"]).updateMask(keep)


def fetch_dynamic_predictors(year: int) -> pd.DataFrame:
    """Per-cell, per-month NDWI, soil moisture, LST for `year`, cached parquet."""
    out = DATA_RAW / f"dynamic_predictors_{year}.parquet"
    if file_exists(out, f"dynamic predictors {year}"):
        return pd.read_parquet(out)

    init_earth_engine()
    grid = build_grid(load_districts())
    grid_cent = grid.to_crs(3857).copy()
    grid_cent["geometry"] = grid_cent.geometry.centroid
    grid_cent = grid_cent.to_crs(4326)
    cell_ids = grid_cent["cell_id"].tolist()

    BATCH = 2000
    recs = []
    for m in tqdm(PREDICTOR_MONTHS, desc=f"dynamic {year} months"):
        start = f"{year}-{m:02d}-01"
        end = f"{year + (m == 12)}-{(m % 12) + 1:02d}-01"  # exclusive

        # NDWI from MODIS surface reflectance (NIR=sur_refl_b02, SWIR=sur_refl_b06)
        # use MOD13A1 NDVI/EVI as vegetation proxy; compute NDWI from MOD09A1
        mod09 = (ee.ImageCollection("MODIS/061/MOD09A1")
                 .filterDate(start, end).map(_mask_mod09))
        if mod09.size().getInfo() > 0:
            ndwi = mod09.map(
                lambda im: im.normalizedDifference(["sur_refl_b02", "sur_refl_b06"]).rename("ndwi")
            ).mean()
        else:
            ndwi = ee.Image.constant(0).updateMask(0).rename("ndwi")

        # Land surface temperature (8-day, day) -> Kelvin*0.02
        mod11 = (ee.ImageCollection("MODIS/061/MOD11A2")
                 .filterDate(start, end).select("LST_Day_1km"))
        if mod11.size().getInfo() > 0:
            lst = mod11.mean().multiply(0.02).rename("lst_k")
        else:
            lst = ee.Image.constant(0).updateMask(0).rename("lst_k")

        # SMAP surface soil moisture
        smap = (ee.ImageCollection("NASA/SMAP/SPL4SMGP/007")
                .filterDate(start, end).select("sm_surface"))
        if smap.size().getInfo() > 0:
            sm = smap.mean().rename("soil_moisture")
        else:
            sm = ee.Image.constant(0).updateMask(0).rename("soil_moisture")

        stack = ndwi.addBands(lst).addBands(sm)

        for i in range(0, len(cell_ids), BATCH):
            batch_ids = cell_ids[i:i + BATCH]
            sub = grid_cent[grid_cent["cell_id"].isin(batch_ids)]
            feats = [
                ee.Feature(ee.Geometry.Point([r.geometry.x, r.geometry.y]),
                           {"cell_id": int(r["cell_id"])})
                for _, r in sub.iterrows()
            ]
            fc_batch = ee.FeatureCollection(feats)
            reduced = stack.reduceRegions(
                collection=fc_batch, reducer=ee.Reducer.mean(), scale=1000)
            for f in reduced.getInfo()["features"]:
                p = f["properties"]
                recs.append({
                    "cell_id": int(p["cell_id"]),
                    "month": m,
                    "ndwi": p.get("ndwi"),
                    "lst_k": p.get("lst_k"),
                    "soil_moisture": p.get("soil_moisture"),
                    "year": year,
                })

    df = pd.DataFrame(recs)

    df.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "Monthly dynamic predictors (NDWI, LST, soil moisture)",
        "source": "MODIS MOD09A1/MOD11A2 + NASA SMAP via GEE",
        "source_url": "https://developers.google.com/earth-engine/datasets",
        "license": "Public domain (NASA)",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "500 m - 9 km, reduced to grid",
        "temporal_coverage": f"{year} May-Nov, monthly",
        "preprocessing_steps": "monthly mean of NDWI (MOD09A1 masked by StateQA for cloud, shadow, "
                               "high aerosol and fire), LST (MOD11A2), SMAP surface soil moisture; "
                               "months without data stored as missing; batched reduceRegions to grid",
        "unit": "ndwi [-1,1]; lst Kelvin; soil_moisture m3/m3",
        "citation_apa": "Entekhabi, D., et al. (2010). The Soil Moisture Active Passive (SMAP) "
                        "mission. Proceedings of the IEEE, 98(5), 704-716.",
        "citation_bibtex": "@article{entekhabi2010smap,title={The Soil Moisture Active Passive "
                           "(SMAP) mission},author={Entekhabi, D. and others},journal={Proceedings "
                           "of the IEEE},volume={98},number={5},pages={704--716},year={2010}}",
        "crs": "EPSG:4326",
    })
    log_step(f"dynamic {year}: {len(df)} cell-month rows", "OK")
    return df
