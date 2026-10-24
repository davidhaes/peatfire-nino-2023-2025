from __future__ import annotations

from pathlib import Path

RANDOM_SEED: int = 42

# analysis grid resolution. Fire labels come from the MODIS-based FIRMS
# raster in Earth Engine (1 km), so a 3 km cell holds about nine fire pixels.
GRID_CELL_KM: float = 3.0

# study years: 2023 strong El Nino peak vs 2024 transition
STUDY_YEARS: tuple[int, ...] = (2023, 2024, 2025)

# dry-season window for peat fires in SUM/KAL (Jun-Nov), peaks Sep-Oct
DRY_SEASON_MONTHS: tuple[int, ...] = (6, 7, 8, 9, 10, 11)

# Predictors are also fetched for the month before the season, so that the
# June row has a real previous-month value instead of a copy of June.
PREDICTOR_MONTHS: tuple[int, ...] = (5,) + DRY_SEASON_MONTHS

# FIRMS in Earth Engine is the MODIS Collection 6.1 active fire product
# rasterised at 1 km (bands T21, confidence, line_number). Detections below
# 30 percent confidence are the product's "low" class and are excluded.
FIRMS_MIN_CONFIDENCE: int = 30

# Forest loss is only used from before the study period. Loss recorded in
# 2023 includes forest killed by the 2023 fires, which would leak the label.
HANSEN_LOSS_LAST_YEAR: int = 2022

# Peat extent and thickness from PEATGRIDS (Widyastuti et al. 2025, CC BY 4.0),
# Earth Engine community catalogue. Indonesian regulation defines peat soil
# as an organic layer at least 50 cm thick.
PEAT_MIN_THICKNESS_CM: float = 50.0
PEAT_CELL_SHARE: float = 0.5

# target districts: (GADM name match, BPS code, province, fallback UTM EPSG)
TARGET_DISTRICTS: tuple[dict, ...] = (
    {"name": "Ogan Komering Ilir", "bps": "1602", "prov": "Sumatera Selatan", "utm": 32748},
    {"name": "Banyuasin",          "bps": "1607", "prov": "Sumatera Selatan", "utm": 32748},
    {"name": "Kotawaringin Timur", "bps": "6202", "prov": "Kalimantan Tengah", "utm": 32749},
    {"name": "Pulang Pisau",       "bps": "6210", "prov": "Kalimantan Tengah", "utm": 32749},
    {"name": "Pelalawan",          "bps": "1405", "prov": "Riau",              "utm": 32748},
)

# VPD threshold (kPa) above which fire likelihood rises sharply in tropical peat.
# Yin et al. 2020 report nonlinear VPD-fire response; value flagged for verification.
VPD_HIGH_KPA: float = 1.5

# Daily fire-pixel quantile used to flag "high-fire-activity" days for smoke analysis
HIGH_ACTIVITY_QUANTILE: float = 0.90

# storage guard thresholds (GB)
STORAGE_WARN_GB: float = 8.0
STORAGE_STOP_GB: float = 10.0

# GEE asset ids used across the project
GEE_ASSETS: dict[str, str] = {
    "era5_land_daily": "ECMWF/ERA5_LAND/DAILY_AGGR",
    "hansen_gfc": "UMD/hansen/global_forest_change_2023_v1_11",
    "merit_dem": "MERIT/DEM/v1_0_3",
    "firms": "FIRMS",
    "mcd64a1": "MODIS/061/MCD64A1",
    "peat_thickness": "projects/sat-io/open-datasets/PEATGRIDS/THICKNESS_CM",
    "oisst": "NOAA/CDR/OISST/V2_1",
}

# GADM 4.1 level-2 (district) source, geopackage per country
GADM_IDN_URL: str = "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_IDN.gpkg"

# Global Peatland Database / SEA peat extent mirror (open) on HDX
# Documented honestly: coverage gaps logged at fetch time.
PEAT_EXTENT_HDX: str = (
    "https://data.humdata.org/dataset/global-peatlands"  # resolved to actual resource at fetch
)


def project_root() -> Path:
    """Return repository root (parent of the src directory)."""
    here = Path(__file__).resolve()
    # config.py -> peatfire_nino -> src -> root
    return here.parents[2]
