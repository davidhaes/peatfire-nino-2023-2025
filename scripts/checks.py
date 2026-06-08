from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from peatfire_nino.io.logging_utils import log_step


def assert_crs_match(*layers: gpd.GeoDataFrame) -> None:
    """Raise if vector layers do not share a CRS."""
    crs_set = {str(l.crs) for l in layers if l is not None}
    if len(crs_set) > 1:
        raise ValueError(f"CRS mismatch across layers: {crs_set}. Reproject before joining.")


def assert_nonempty(gdf: gpd.GeoDataFrame, name: str) -> None:
    if gdf is None or gdf.empty:
        raise ValueError(f"layer '{name}' is empty; upstream fetch likely failed.")
    log_step(f"check ok: {name} has {len(gdf)} rows", "INFO")


def file_exists(path: Path, hint: str) -> bool:
    if path.exists():
        log_step(f"Using cached file {path.name}", "INFO")
        return True
    log_step(f"Downloading fresh: {hint}", "INFO")
    return False
