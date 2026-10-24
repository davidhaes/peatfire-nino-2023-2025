"""firms.py
Active fire labels from the FIRMS collection in Earth Engine.

What the collection is
----------------------
`ee.ImageCollection("FIRMS")` is the MODIS Collection 6.1 active fire product
(Terra and Aqua) rasterised to 1 km, one image per day, with bands `T21`
(band 21 brightness temperature, Kelvin), `confidence` (0-100) and
`line_number`. It is not the VIIRS 375 m product, and it carries no fire
radiative power. An earlier version of this module described it as VIIRS
and stored `T21` in a column called `frp`.

How labels are built
--------------------
For every analysis cell and month the number of 1 km fire pixels is counted
directly with `reduceRegions`. The earlier version vectorised the monthly
fire mask with `reduceToVectors`, which merges every connected group of fire
pixels into one polygon and kept only its centroid. A burning peat complex of
hundreds of square kilometres became one point, so one cell was labelled as
burning and every other burning cell as not burning. In September 2023 that
kept 203 records against 5,480 fire pixels in the five districts.

Daily counts per district are fetched separately for the smoke analysis,
which needs to know which *days* were high-activity days.
"""
from __future__ import annotations

from datetime import date

import ee
import pandas as pd
from tqdm import tqdm

from peatfire_nino.config import DRY_SEASON_MONTHS, FIRMS_MIN_CONFIDENCE, GEE_ASSETS
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW

BATCH = 1000

_METADATA = {
    "source": "NASA FIRMS, MODIS Collection 6.1 active fire (MOD14/MYD14), via Google Earth Engine",
    "source_url": "https://developers.google.com/earth-engine/datasets/catalog/FIRMS",
    "license": "Public domain (NASA EOSDIS)",
    "spatial_resolution": "1 km (rasterised MODIS active fire)",
    "citation_apa": "Giglio, L., Schroeder, W., & Justice, C. O. (2016). The collection 6 MODIS "
                    "active fire detection algorithm and fire products. Remote Sensing of "
                    "Environment, 178, 31-41.",
    "citation_bibtex": "@article{giglio2016c6,title={The collection 6 MODIS active fire detection "
                       "algorithm and fire products},author={Giglio, L. and Schroeder, W. and "
                       "Justice, C. O.},journal={Remote Sensing of Environment},volume={178},"
                       "pages={31--41},year={2016}}",
    "crs": "EPSG:4326",
}


def month_window(year: int, month: int) -> tuple[str, str]:
    """Start inclusive, end exclusive, so the last day of the month is kept."""
    start = f"{year}-{month:02d}-01"
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    return start, f"{ny}-{nm:02d}-01"


def _fire_mask(image: ee.Image) -> ee.Image:
    conf = image.select("confidence")
    return image.select("T21").gt(0).And(conf.gte(FIRMS_MIN_CONFIDENCE)).rename("fire")


def fetch_firms(year: int) -> pd.DataFrame:
    """Fire pixels per analysis cell and month for the dry season of `year`.

    Columns: cell_id, month, year, n_fire_px (1 km pixels that burned on at
    least one day of the month), n_fire_days_px (pixel-days, the sum over
    days), t21_mean (mean brightness temperature of fire pixels, Kelvin).
    Only cell-months with at least one fire pixel are returned.
    """
    out = DATA_RAW / f"firms_modis_cells_{year}.parquet"
    if file_exists(out, f"FIRMS MODIS cell counts {year}"):
        return pd.read_parquet(out)

    init_earth_engine()
    grid = build_grid(load_districts())
    features = [
        ee.Feature(ee.Geometry(geom.__geo_interface__), {"cell_id": int(cid)})
        for cid, geom in zip(grid["cell_id"], grid.geometry)
    ]

    recs = []
    for m in tqdm(DRY_SEASON_MONTHS, desc=f"FIRMS {year} months"):
        start, end = month_window(year, m)
        raw = ee.ImageCollection(GEE_ASSETS["firms"]).filterDate(start, end)
        if raw.size().getInfo() == 0:
            continue
        daily = raw.map(_fire_mask)
        counts_img = daily.max().rename("n_fire_px").addBands(daily.sum().rename("n_fire_days_px"))
        t21 = raw.map(lambda im: im.select("T21").updateMask(_fire_mask(im))).mean().rename("t21_mean")

        for i in range(0, len(features), BATCH):
            fc = ee.FeatureCollection(features[i:i + BATCH])
            counts = counts_img.unmask(0).reduceRegions(collection=fc, reducer=ee.Reducer.sum(), scale=1000)
            temps = t21.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=1000)
            t_by_cell = {f["properties"]["cell_id"]: f["properties"].get("mean")
                         for f in temps.getInfo()["features"]}
            for f in counts.getInfo()["features"]:
                p = f["properties"]
                n = p.get("n_fire_px") or 0
                if n <= 0:
                    continue
                recs.append({
                    "cell_id": int(p["cell_id"]),
                    "month": m,
                    "year": year,
                    "n_fire_px": float(n),
                    "n_fire_days_px": float(p.get("n_fire_days_px") or 0),
                    "t21_mean": t_by_cell.get(p["cell_id"]),
                })

    df = pd.DataFrame(recs, columns=["cell_id", "month", "year", "n_fire_px", "n_fire_days_px", "t21_mean"])
    df.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "MODIS active fire pixels per 3 km cell and month",
        "access_date": date.today().isoformat(),
        "temporal_coverage": f"{year} dry season (Jun-Nov), monthly",
        "preprocessing_steps": (
            f"daily FIRMS images, fire = T21 > 0 and confidence >= {FIRMS_MIN_CONFIDENCE}; "
            "per month: any-day fire mask and pixel-day sum; reduceRegions sum over each 3 km "
            "cell at 1 km scale; mean T21 of fire pixels"
        ),
        "unit": "count of 1 km fire pixels; T21 Kelvin",
        **_METADATA,
    })
    log_step(f"FIRMS {year}: {len(df)} burning cell-months, "
             f"{int(df['n_fire_px'].sum()) if len(df) else 0} fire pixel-months", "OK")
    return df


def fetch_firms_daily(year: int) -> pd.DataFrame:
    """Fire pixels per district and day for the dry season of `year`."""
    out = DATA_RAW / f"firms_modis_daily_{year}.parquet"
    if file_exists(out, f"FIRMS MODIS daily counts {year}"):
        return pd.read_parquet(out)

    init_earth_engine()
    districts = load_districts()
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(row.geometry.__geo_interface__), {"district": row["district"]})
        for _, row in districts.iterrows()
    ])
    start = f"{year}-{DRY_SEASON_MONTHS[0]:02d}-01"
    _, end = month_window(year, DRY_SEASON_MONTHS[-1])
    daily = ee.ImageCollection(GEE_ASSETS["firms"]).filterDate(start, end)

    def per_day(im):
        stats = _fire_mask(im).unmask(0).reduceRegions(collection=fc, reducer=ee.Reducer.sum(), scale=1000)
        d = im.date().format("YYYY-MM-dd")
        return stats.map(lambda f: f.set("date", d))

    rows = []
    n = daily.size().getInfo()
    images = daily.toList(n)
    for i in tqdm(range(0, n, 30), desc=f"FIRMS daily {year}"):
        chunk = ee.ImageCollection(images.slice(i, i + 30))
        feats = chunk.map(per_day).flatten().getInfo()["features"]
        for f in feats:
            p = f["properties"]
            rows.append({"district": p["district"], "date": p["date"], "n_fire_px": float(p.get("sum") or 0)})

    df = pd.DataFrame(rows, columns=["district", "date", "n_fire_px"])
    df["date"] = pd.to_datetime(df["date"])
    df.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "MODIS active fire pixels per district and day",
        "access_date": date.today().isoformat(),
        "temporal_coverage": f"{year} dry season (Jun-Nov), daily",
        "preprocessing_steps": f"daily FIRMS images, confidence >= {FIRMS_MIN_CONFIDENCE}, sum over district",
        "unit": "count of 1 km fire pixels",
        **_METADATA,
    })
    log_step(f"FIRMS daily {year}: {len(df)} district-days", "OK")
    return df
