"""fuel_terrain.py
Hansen tree-cover fuel and MERIT DEM terrain predictors reduced to the grid (batched).
"""
from __future__ import annotations

from datetime import date

import ee
import pandas as pd
from tqdm import tqdm

from peatfire_nino.config import GEE_ASSETS, HANSEN_LOSS_LAST_YEAR
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW


def fetch_fuel_terrain() -> pd.DataFrame:
    """Per-cell tree cover, forest-loss flag, elevation, slope. Cached parquet."""
    out = DATA_RAW / "fuel_terrain.parquet"
    if file_exists(out, "fuel + terrain"):
        return pd.read_parquet(out)

    init_earth_engine()
    grid = build_grid(load_districts())

    grid_cent = grid.to_crs(3857).copy()
    grid_cent["geometry"] = grid_cent.geometry.centroid
    grid_cent = grid_cent.to_crs(4326)
    cell_ids = grid_cent["cell_id"].tolist()

    hansen = ee.Image(GEE_ASSETS["hansen_gfc"])
    treecover = hansen.select("treecover2000").rename("treecover")
    loss = hansen.select("lossyear")
    # Loss up to the year before the study period only. Loss recorded in 2023
    # includes forest killed by the 2023 fires and would leak the label.
    loss_recent = loss.gte(1).And(loss.lte(HANSEN_LOSS_LAST_YEAR - 2000)).rename("loss_flag")
    dem = ee.Image(GEE_ASSETS["merit_dem"]).rename("elevation")
    slope = ee.Terrain.slope(dem).rename("slope")
    stack = treecover.addBands(loss_recent).addBands(dem).addBands(slope)

    BATCH = 2000
    recs = []
    for i in tqdm(range(0, len(cell_ids), BATCH), desc="fuel/terrain batches"):
        batch_ids = cell_ids[i:i + BATCH]
        sub = grid_cent[grid_cent["cell_id"].isin(batch_ids)]
        feats = [
            ee.Feature(ee.Geometry.Point([r.geometry.x, r.geometry.y]),
                       {"cell_id": int(r["cell_id"])})
            for _, r in sub.iterrows()
        ]
        fc_batch = ee.FeatureCollection(feats)
        reduced = stack.reduceRegions(collection=fc_batch,
                                      reducer=ee.Reducer.mean(), scale=1000)
        for f in reduced.getInfo()["features"]:
            p = f["properties"]
            recs.append({
                "cell_id": int(p["cell_id"]),
                "treecover": p.get("treecover"),
                "loss_frac": p.get("loss_flag"),
                "elevation": p.get("elevation"),
                "slope": p.get("slope"),
            })
    df = pd.DataFrame(recs)

    df.to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "Hansen GFC tree cover/loss + MERIT DEM terrain",
        "source": "Hansen/UMD/Google; MERIT DEM (Yamazaki) via GEE",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/"
                      "UMD_hansen_global_forest_change_2023_v1_11",
        "license": "CC-BY 4.0 (Hansen GFC); MERIT DEM free for research",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "30 m (Hansen), ~90 m (MERIT), reduced to grid",
        "temporal_coverage": f"tree cover 2000 baseline; loss 2001-{HANSEN_LOSS_LAST_YEAR}",
        "preprocessing_steps": f"select treecover2000, loss 2001-{HANSEN_LOSS_LAST_YEAR} flag, slope from MERIT, "
                               "batched reduceRegions mean to grid",
        "unit": "treecover % ; loss_frac 0-1 ; elevation m ; slope deg",
        "citation_apa": "Hansen, M. C., et al. (2013). High-resolution global maps of "
                        "21st-century forest cover change. Science, 342(6160), 850-853.",
        "citation_bibtex": "@article{hansen2013forest,title={High-resolution global maps of "
                           "21st-century forest cover change},author={Hansen, M. C. and others},"
                           "journal={Science},volume={342},number={6160},pages={850--853},"
                           "year={2013}}",
        "crs": "EPSG:4326",
    })
    log_step(f"fuel+terrain: {len(df)} cells", "OK")
    return df
