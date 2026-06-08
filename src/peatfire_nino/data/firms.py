"""firms.py
Fetch VIIRS active fire from Earth Engine FIRMS collection, per month.
Preserves monthly temporal resolution for hotspot and climate matching.
"""
from __future__ import annotations

import calendar
from datetime import date

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from tqdm import tqdm

from peatfire_nino.config import DRY_SEASON_MONTHS
from peatfire_nino.data.aoi import load_districts
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW


def fetch_firms(year: int) -> gpd.GeoDataFrame:
    """Return VIIRS fire-affected cells within AOI for dry-season `year`, per month."""
    out = DATA_RAW / f"firms_viirs_{year}.gpkg"
    if file_exists(out, f"FIRMS VIIRS {year}"):
        return gpd.read_file(out)

    init_earth_engine()
    aoi = load_districts()
    region = ee.Geometry(aoi.unary_union.__geo_interface__)

    all_recs = []
    for m in tqdm(DRY_SEASON_MONTHS, desc=f"FIRMS {year} months"):
        last_day = calendar.monthrange(year, m)[1]
        start = f"{year}-{m:02d}-01"
        end = f"{year}-{m:02d}-{last_day:02d}"

        coll = (ee.ImageCollection("FIRMS")
                .filterDate(start, end)
                .filterBounds(region)
                .select("T21"))
        if coll.size().getInfo() == 0:
            continue

        fire_img = coll.max().rename("bright")
        fire_mask = fire_img.gt(0)
        vectors = fire_mask.selfMask().reduceToVectors(
            geometry=region, scale=1000, geometryType="centroid",
            maxPixels=1e10, bestEffort=True,
        )
        vectors = fire_img.reduceRegions(
            collection=vectors, reducer=ee.Reducer.mean(), scale=1000)

        feats = vectors.getInfo()["features"]
        for f in feats:
            geom = f["geometry"]["coordinates"]
            p = f["properties"]
            all_recs.append({
                "longitude": geom[0],
                "latitude": geom[1],
                "frp": p.get("mean") or p.get("bright") or 0.0,
                "acq_date": f"{year}-{m:02d}-15",
                "month": m,
            })

    if not all_recs:
        raise RuntimeError(f"No FIRMS records from GEE for {year} in AOI.")

    df = pd.DataFrame(all_recs)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
        crs=4326,
    )
    gdf = gpd.sjoin(gdf, aoi[["district", "geometry"]], predicate="within", how="inner")
    gdf = gdf.drop(columns="index_right")
    gdf["frp"] = pd.to_numeric(gdf["frp"], errors="coerce")
    gdf = gdf.dropna(subset=["frp"])

    gdf.to_file(out, driver="GPKG")
    write_metadata(out, {
        "dataset_name": "NASA FIRMS VIIRS active fire (via Earth Engine, monthly)",
        "source": "NASA FIRMS / LANCE via Google Earth Engine",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/FIRMS",
        "license": "Public domain (NASA EOSDIS)",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "~1 km (FIRMS EE product)",
        "temporal_coverage": f"{year} dry season (Jun-Nov), monthly bins",
        "preprocessing_steps": "EE FIRMS T21 max per month, vectorise fire pixels to centroids "
                               "at 1 km, clip to district polygons, retain month",
        "unit": "brightness temperature (K) as fire-intensity proxy",
        "citation_apa": "Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The New "
                        "VIIRS 375 m active fire detection data product. Remote Sensing of "
                        "Environment, 143, 85-96.",
        "citation_bibtex": "@article{schroeder2014viirs,title={The New VIIRS 375 m active fire "
                           "detection data product},author={Schroeder, W. and others},"
                           "journal={Remote Sensing of Environment},volume={143},pages={85--96},"
                           "year={2014}}",
        "crs": "EPSG:4326",
    })
    n_cells = gdf[["latitude", "longitude"]].drop_duplicates().shape[0]
    log_step(f"FIRMS {year}: {len(gdf)} cell-month fire records, {n_cells} unique cells", "OK")
    return gdf
