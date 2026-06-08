from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from peatfire_nino.config import GADM_IDN_URL, GRID_CELL_KM, TARGET_DISTRICTS
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW

_AOI_PATH = DATA_RAW / "aoi_districts.gpkg"


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def load_districts() -> gpd.GeoDataFrame:
    """Return the 5 target districts as a GeoDataFrame (EPSG:4326), cached."""
    if _AOI_PATH.exists():
        log_step(f"Using cached AOI {_AOI_PATH.name}", "INFO")
        return gpd.read_file(_AOI_PATH)

    log_step("Downloading GADM level-2 (IDN) districts", "INFO")
    # layer ADM_ADM_2 holds districts in GADM 4.1 gpkg
    gdf = gpd.read_file(f"{GADM_IDN_URL}", layer="ADM_ADM_2")

    wanted = {_norm(d["name"]): d for d in TARGET_DISTRICTS}
    gdf["_key"] = gdf["NAME_2"].astype(str).map(_norm)
    sel = gdf[gdf["_key"].isin(wanted.keys())].copy()

    if sel["_key"].nunique() < len(wanted):
        found = set(sel["_key"].unique())
        missing = [wanted[k]["name"] for k in wanted if k not in found]
        # GADM spelling can differ; log honestly rather than silently drop
        log_step(f"Districts not matched by exact name: {missing}", "WARN")

    sel["bps"] = sel["_key"].map(lambda k: wanted.get(k, {}).get("bps"))
    sel["utm_epsg"] = sel["_key"].map(lambda k: wanted.get(k, {}).get("utm"))
    sel = sel[["NAME_1", "NAME_2", "bps", "utm_epsg", "geometry"]].rename(
        columns={"NAME_1": "province", "NAME_2": "district"}
    )
    sel = sel.to_crs(4326).reset_index(drop=True)

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    sel.to_file(_AOI_PATH, driver="GPKG")
    write_metadata(_AOI_PATH, {
        "dataset_name": "GADM 4.1 level-2 districts (subset)",
        "source": "GADM",
        "source_url": GADM_IDN_URL,
        "license": "Free for academic/non-commercial use (GADM license)",
        "access_date": _today(),
        "spatial_resolution": "vector polygons",
        "temporal_coverage": "GADM 4.1 (2022 release)",
        "preprocessing_steps": "read gpkg ADM_ADM_2, filter 5 target districts, reproject EPSG:4326",
        "unit": "n/a",
        "citation_apa": "Global Administrative Areas (2022). GADM database of Global "
                        "Administrative Areas, version 4.1. https://gadm.org",
        "citation_bibtex": "@misc{gadm41,title={GADM database v4.1},author={{GADM}},"
                           "year={2022},url={https://gadm.org}}",
        "crs": "EPSG:4326",
    })
    log_step(f"Saved AOI with {len(sel)} districts", "OK")
    return sel


def build_grid(districts: gpd.GeoDataFrame, cell_km: float = GRID_CELL_KM) -> gpd.GeoDataFrame:
    """Build a per-region square grid (cell_km) clipped to district extents."""
    out_path = DATA_RAW / "analysis_grid.gpkg"
    if out_path.exists():
        log_step(f"Using cached grid {out_path.name}", "INFO")
        return gpd.read_file(out_path)

    frames = []
    cell_m = cell_km * 1000.0
    for epsg, grp in districts.groupby("utm_epsg"):
        proj = grp.to_crs(int(epsg))
        minx, miny, maxx, maxy = proj.total_bounds
        nx = int(math.ceil((maxx - minx) / cell_m))
        ny = int(math.ceil((maxy - miny) / cell_m))
        cells = []
        for i in range(nx):
            for j in range(ny):
                x0 = minx + i * cell_m
                y0 = miny + j * cell_m
                cells.append(box(x0, y0, x0 + cell_m, y0 + cell_m))
        grid = gpd.GeoDataFrame({"geometry": cells}, crs=int(epsg))
        # keep only cells intersecting the districts
        joined = gpd.sjoin(grid, proj[["district", "bps", "geometry"]],
                           predicate="intersects", how="inner")
        joined = joined.drop(columns="index_right").to_crs(4326)
        frames.append(joined)

    grid_all = gpd.GeoDataFrame(
        np.nan_to_num if False else __import__("pandas").concat(frames, ignore_index=True),
        crs=4326,
    )
    grid_all = grid_all.reset_index(drop=True)
    grid_all["cell_id"] = grid_all.index.astype(int)
    grid_all.to_file(out_path, driver="GPKG")
    log_step(f"Built analysis grid: {len(grid_all)} cells at {cell_km} km", "OK")
    return grid_all


def _today() -> str:
    from datetime import date
    return date.today().isoformat()
