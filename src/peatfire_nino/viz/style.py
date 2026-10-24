"""style.py
Shared cartographic and chart style: palettes, pretty labels, glossary,
basemap config, layout helpers. One consistent professional look.
"""
from __future__ import annotations

import matplotlib.patheffects as pe

DPI = 300
BOUNDARY = "#15171a"
BW = 1.1
HALO = [pe.withStroke(linewidth=3.0, foreground="white")]
SRC = "Data: NASA FIRMS (MODIS), ERA5-Land, Hansen GFC, MERIT DEM, PEATGRIDS, GADM 4.1"

# basemap: "relief" (shaded topo), "gray", "voyager", "positron", "imagery", "dark"
BASEMAP = "relief"

PALETTES = {"susceptibility": "YlOrRd", "diverging": "RdBu_r",
            "interaction": "#3f6f73", "shap": "#b63a1c"}

PRETTY = {
    "ndwi": "NDWI", "vpd": "VPD (kPa)", "lst_k": "LST (K)", "soil_moisture": "Soil moisture (m³/m³)",
    "treecover": "Tree cover 2000 (%)", "loss_frac": "Forest loss to 2022 (share)", "elevation": "Elevation (m)",
    "slope": "Slope (degrees)", "peat_likely": "Peat (PEATGRIDS)", "wind_speed": "Wind speed (m/s)",
    "peat_share": "Peat share", "peat_thickness_cm": "Peat thickness (cm)",
    "ndwi_lag1": "NDWI, previous month", "lst_lag1": "LST, previous month (K)",
    "precip_mm": "Rainfall (mm/day)", "precip_lag1": "Rainfall, previous month (mm/day)",
    "vpd_lag1": "VPD, previous month (kPa)", "sm_lag1": "Soil moisture, previous month (m³/m³)",
    "precip_cum2": "Rainfall, this and previous month (mm/day)",
}
# Precipitation is the monthly mean of ERA5-Land daily totals, so its unit is
# mm per day; precip_cum2 adds this month's and last month's daily means.
GLOSSARY = ("NDWI: Normalized Difference Water Index   |   VPD: Vapour Pressure Deficit"
            "   |   LST: Land Surface Temperature")

# label offsets (dx, dy degrees) per district, into empty space, no leader lines
LABEL_OFFSET = {
    "Pelalawan": (0.0, 0.55),
    "Banyu Asin": (-0.65, 0.30),
    "Ogan Komering Ilir": (0.10, -0.70),
    "Kotawaringin Timur": (-0.55, -0.75),
    "Pulang Pisau": (0.65, -0.20),
}


def pretty(name: str) -> str:
    return PRETTY.get(name, name.replace("_", " ").title())


def basemap_provider():
    import contextily as cx
    return {
        "relief": cx.providers.Esri.WorldShadedRelief,
        "gray": cx.providers.Esri.WorldGrayCanvas,
        "voyager": cx.providers.CartoDB.VoyagerNoLabels,
        "positron": cx.providers.CartoDB.PositronNoLabels,
        "imagery": cx.providers.Esri.WorldImagery,
        "dark": cx.providers.CartoDB.DarkMatterNoLabels,
    }.get(BASEMAP, cx.providers.Esri.WorldShadedRelief)
