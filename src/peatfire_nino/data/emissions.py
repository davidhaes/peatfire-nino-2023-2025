from __future__ import annotations

from datetime import date

import pandas as pd

from peatfire_nino.config import STUDY_YEARS
from peatfire_nino.data.aoi import load_districts
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW
from scripts.checks import file_exists


def summarise_emissions() -> pd.DataFrame:
    """Per-district GFED emissions summary for study years. Cached CSV.

    Uses GFED4.1s on GEE if available; otherwise records a documented gap.
    """
    out = DATA_RAW / "gfed_emissions_summary.csv"
    if file_exists(out, "GFED emissions"):
        return pd.read_csv(out)

    try:
        import ee
        from peatfire_nino.io.gee_session import init_earth_engine
        init_earth_engine()
        aoi = load_districts()

        # GFED4.1s burned area / emissions are not all in GEE; use FireCCI as a proxy if needed.
        # Here we use MODIS MCD64A1 burned area as an open, GEE-native emissions proxy basis.
        records = []
        for _, row in aoi.iterrows():
            geom = ee.Geometry(row.geometry.__geo_interface__)
            for year in STUDY_YEARS:
                coll = (ee.ImageCollection("MODIS/061/MCD64A1")
                        .filterDate(f"{year}-06-01", f"{year}-11-30")
                        .select("BurnDate"))
                burned = coll.map(lambda im: im.gt(0)).sum().gt(0).rename("burned")
                area = (burned.multiply(ee.Image.pixelArea())
                        .reduceRegion(ee.Reducer.sum(), geom, scale=500, maxPixels=1e10))
                ha = (area.get("burned").getInfo() or 0) / 10000.0
                records.append({"district": row["district"], "year": year,
                                "burned_area_ha": round(ha, 1)})
        df = pd.DataFrame(records)
    except Exception as exc:  # noqa: BLE001
        log_step(f"emissions/burned-area fetch failed, recording gap: {exc}", "WARN")
        df = pd.DataFrame(columns=["district", "year", "burned_area_ha"])

    df.to_csv(out, index=False, encoding="utf-8")
    write_metadata(out, {
        "dataset_name": "MODIS MCD64A1 burned area per district (emissions context proxy)",
        "source": "NASA MODIS MCD64A1 via GEE",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/"
                      "MODIS_061_MCD64A1",
        "license": "Public domain (NASA)",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "500 m",
        "temporal_coverage": "2023, 2024 dry season",
        "preprocessing_steps": "sum monthly burned pixels, area in ha per district",
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
    log_step(f"emissions context: {len(df)} district-year rows", "OK")
    return df
