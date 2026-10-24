"""peat.py
Peat extent per analysis cell from PEATGRIDS.

The earlier version flagged a cell as peat when its mean elevation was 25 m
or less. That marked 6,531 of 8,314 cells (79 percent of the study area) as
peat, including mineral-soil floodplain and coastal lowland, and the model
ranked the flag last among all predictors.

This version reads peat thickness from PEATGRIDS (Widyastuti et al. 2025,
1 km, CC BY 4.0), published in the Earth Engine community catalogue, and
records for every cell the share of its area where mean peat thickness is at
least 50 cm, the thickness Indonesian regulation uses to define peat soil.
A cell is `peat_likely` when that share is at least one half; the share and
the mean thickness are kept as continuous predictors.
"""
from __future__ import annotations

from datetime import date

import ee
import pandas as pd

from peatfire_nino.config import GEE_ASSETS, PEAT_CELL_SHARE, PEAT_MIN_THICKNESS_CM
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW

BATCH = 1000


def peat_mask_image() -> ee.Image:
    """1 where PEATGRIDS mean thickness is at least the regulatory minimum."""
    thick = ee.Image(GEE_ASSETS["peat_thickness"]).select("THICKNESS_CM_MEAN")
    return thick.gte(PEAT_MIN_THICKNESS_CM).unmask(0).rename("peat")


def fetch_peat_extent() -> pd.DataFrame:
    """Per-cell peat share, mean thickness and binary flag. Cached parquet."""
    out = DATA_RAW / "peat_peatgrids.parquet"
    if file_exists(out, "PEATGRIDS peat extent"):
        return pd.read_parquet(out)

    init_earth_engine()
    grid = build_grid(load_districts())
    thick = ee.Image(GEE_ASSETS["peat_thickness"]).select("THICKNESS_CM_MEAN").unmask(0).rename("peat_thickness_cm")
    stack = peat_mask_image().rename("peat_share").addBands(thick)
    features = [
        ee.Feature(ee.Geometry(geom.__geo_interface__), {"cell_id": int(cid)})
        for cid, geom in zip(grid["cell_id"], grid.geometry)
    ]
    rows = []
    for i in range(0, len(features), BATCH):
        fc = ee.FeatureCollection(features[i:i + BATCH])
        reduced = stack.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=1000)
        for f in reduced.getInfo()["features"]:
            p = f["properties"]
            rows.append({
                "cell_id": int(p["cell_id"]),
                "peat_share": float(p.get("peat_share") or 0.0),
                "peat_thickness_cm": float(p.get("peat_thickness_cm") or 0.0),
            })
    df = pd.DataFrame(rows)
    df["peat_likely"] = (df["peat_share"] >= PEAT_CELL_SHARE).astype(int)
    df.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "Peat share and thickness per 3 km cell (PEATGRIDS)",
        "source": "PEATGRIDS, Widyastuti et al. (2025), Earth Engine community catalogue",
        "source_url": "https://gee-community-catalog.org/ (asset projects/sat-io/open-datasets/PEATGRIDS)",
        "license": "CC BY 4.0",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "1 km source, aggregated to 3 km cells",
        "temporal_coverage": "static",
        "preprocessing_steps": (
            f"peat = mean thickness >= {PEAT_MIN_THICKNESS_CM:g} cm; share of each cell under peat "
            f"(area-weighted mean at 1 km); peat_likely = share >= {PEAT_CELL_SHARE:g}"
        ),
        "unit": "share 0-1; thickness cm; flag 0/1",
        "citation_apa": "Widyastuti, M. T., et al. (2025). PEATGRIDS peat thickness and carbon "
                        "stock grids. Earth Engine community catalogue. Verify the full reference "
                        "before publication.",
        "citation_bibtex": "@misc{widyastuti2025peatgrids,title={PEATGRIDS},"
                           "author={Widyastuti, M. T. and others},year={2025}}",
        "crs": "EPSG:4326",
    })
    log_step(f"PEATGRIDS peat: {int(df['peat_likely'].sum())}/{len(df)} cells at least "
             f"{PEAT_CELL_SHARE:.0%} peat", "OK")
    return df[["cell_id", "peat_share", "peat_thickness_cm", "peat_likely"]]
