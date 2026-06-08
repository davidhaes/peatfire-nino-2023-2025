from __future__ import annotations

from pathlib import Path

RANDOM_SEED: int = 42

# analysis grid resolution; VIIRS native ~375 m, aggregated to 1 km for stability
GRID_CELL_KM: float = 3.0

# study years: 2023 strong El Nino peak vs 2024 transition
STUDY_YEARS: tuple[int, ...] = (2023, 2024, 2025)

# dry-season window for peat fires in SUM/KAL (Jun-Nov), peaks Sep-Oct
DRY_SEASON_MONTHS: tuple[int, ...] = (6, 7, 8, 9, 10, 11)

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

# FRP density quantile used to flag "high-fire-activity" days for smoke analysis
HIGH_ACTIVITY_QUANTILE: float = 0.90

# storage guard thresholds (GB)
STORAGE_WARN_GB: float = 8.0
STORAGE_STOP_GB: float = 10.0

# GEE asset ids used across the project
GEE_ASSETS: dict[str, str] = {
    "era5_land_daily": "ECMWF/ERA5_LAND/DAILY_AGGR",
    "hansen_gfc": "UMD/hansen/global_forest_change_2023_v1_11",
    "merit_dem": "MERIT/DEM/v1_0_3",
    "modis_fire": "MODIS/061/MOD14A1",
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
