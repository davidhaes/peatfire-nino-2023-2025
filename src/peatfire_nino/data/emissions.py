"""emissions.py
MODIS MCD64A1 burned area per district and dry season, split into peat and
non-peat by PEATGRIDS.

The earlier version summed burned area over whole districts and then applied
peat fuel consumption to all of it, so burned mineral soil and grassland were
costed as deep peat. It also covered 2023 and 2024 only while the reports
described 2023 to 2025. Both are corrected here.
"""
from __future__ import annotations

from datetime import date

import ee
import pandas as pd

from peatfire_nino.config import DRY_SEASON_MONTHS, GEE_ASSETS, STUDY_YEARS
from peatfire_nino.data.aoi import load_districts
from peatfire_nino.data.firms import month_window
from peatfire_nino.data.peat import peat_mask_image
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW


def summarise_emissions() -> pd.DataFrame:
    """Burned hectares per district and year, on peat and off peat. Cached CSV."""
    out = DATA_RAW / "burned_area_mcd64a1.csv"
    if file_exists(out, "MCD64A1 burned area"):
        return pd.read_csv(out)

    init_earth_engine()
    aoi = load_districts()
    peat = peat_mask_image()
    records = []
    for _, row in aoi.iterrows():
        geom = ee.Geometry(row.geometry.__geo_interface__)
        for year in STUDY_YEARS:
            start, _ = month_window(year, DRY_SEASON_MONTHS[0])
            _, end = month_window(year, DRY_SEASON_MONTHS[-1])
            coll = ee.ImageCollection(GEE_ASSETS["mcd64a1"]).filterDate(start, end).select("BurnDate")
            n_images = coll.size().getInfo()
            if n_images < len(DRY_SEASON_MONTHS):
                log_step(f"MCD64A1 {year}: only {n_images} of {len(DRY_SEASON_MONTHS)} months available", "WARN")
            burned = coll.map(lambda im: im.gt(0)).max().unmask(0)
            area = ee.Image.pixelArea().divide(10000)
            stack = (area.updateMask(burned).rename("burned_ha")
                     .addBands(area.updateMask(burned.And(peat)).rename("burned_peat_ha")))
            sums = stack.reduceRegion(ee.Reducer.sum(), geom, scale=500, maxPixels=1e10).getInfo()
            total = float(sums.get("burned_ha") or 0.0)
            on_peat = float(sums.get("burned_peat_ha") or 0.0)
            records.append({
                "district": row["district"], "year": year,
                "burned_area_ha": round(total, 1),
                "burned_peat_ha": round(on_peat, 1),
                "burned_nonpeat_ha": round(total - on_peat, 1),
                "months_available": int(n_images),
            })
    df = pd.DataFrame(records)
    df.to_csv(out, index=False, encoding="utf-8")
    write_metadata(out, {
        "dataset_name": "MODIS MCD64A1 burned area per district, peat and non-peat",
        "source": "NASA MODIS MCD64A1 via GEE; peat from PEATGRIDS",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD64A1",
        "license": "Public domain (NASA); PEATGRIDS CC BY 4.0",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "500 m",
        "temporal_coverage": f"{STUDY_YEARS[0]}-{STUDY_YEARS[-1]} dry season (Jun-Nov)",
        "preprocessing_steps": "burned if BurnDate > 0 in any month of the season; pixel area summed per "
                               "district, and separately where PEATGRIDS thickness >= 50 cm",
        "unit": "hectares burned",
        "citation_apa": "Giglio, L., Boschetti, L., Roy, D. P., et al. (2018). The Collection 6 "
                        "MODIS burned area mapping algorithm and product. Remote Sensing of "
                        "Environment, 217, 72-85.",
        "citation_bibtex": "@article{giglio2018mcd64,title={The Collection 6 MODIS burned area "
                           "mapping algorithm and product},author={Giglio, L. and Boschetti, L. "
                           "and Roy, D. P. and others},journal={Remote Sensing of Environment},"
                           "volume={217},pages={72--85},year={2018}}",
        "crs": "EPSG:4326",
    })
    log_step(f"burned area: {len(df)} district-year rows", "OK")
    return df
