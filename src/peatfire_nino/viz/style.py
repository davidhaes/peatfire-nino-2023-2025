"""style.py
Shared cartographic and chart style: palettes, pretty labels, glossary,
basemap config, layout helpers. One consistent professional look.
"""
from __future__ import annotations

import matplotlib.patheffects as pe

DPI = 300
BOUNDARY = "#222222"
BW = 1.1
HALO = [pe.withStroke(linewidth=3.0, foreground="white")]
SRC = "Data: NASA FIRMS, ERA5-Land, Hansen GFC, MERIT DEM, GADM 4.1"

# basemap: "relief" (shaded topo), "gray", "voyager", "positron", "imagery", "dark"
BASEMAP = "relief"

PALETTES = {"susceptibility": "YlOrRd", "diverging": "RdBu_r",
            "interaction": "#6A1B9A", "shap": "#B30000"}

PRETTY = {
    "ndwi": "NDWI", "vpd": "VPD", "lst_k": "LST", "soil_moisture": "Soil Moisture",
    "treecover": "Tree Cover", "loss_frac": "Forest Loss", "elevation": "Elevation",
    "slope": "Slope", "peat_likely": "Peat (proxy)", "wind_speed": "Wind Speed",
    "precip_mm": "Precipitation", "precip_lag1": "Precip (prev month)",
    "vpd_lag1": "VPD (prev month)", "sm_lag1": "Soil Moisture (prev month)",
    "precip_cum2": "Precip (2-month sum)",
}
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
