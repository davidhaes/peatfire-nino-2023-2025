"""interactive.py
One self-contained HTML map with layer control.

Layers: observed MODIS fire per cell and season, modelled susceptibility per
season (mean over dry-season months), priority hotspots, peat extent and the
smoke-direction proxy. Each cell is drawn once per layer; the earlier version
drew one polygon per cell per month on top of each other and scaled colours
from 0 to 1 while monthly probabilities sit far below that.
"""
from __future__ import annotations

import branca.colormap as cm
import folium
import pandas as pd

from peatfire_nino.config import STUDY_YEARS
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_INTERACTIVE


def _geojson(gdf, cols):
    """Cells as GeoJSON with coordinates rounded to about 10 m, which keeps the
    file small enough to load in a browser without changing what is drawn."""
    import json

    import shapely

    out = gdf[cols + ["geometry"]].copy()
    out["geometry"] = shapely.set_precision(out.geometry.values, 0.0001)
    data = json.loads(out.to_json(drop_id=True))
    return json.dumps(data, separators=(",", ":"))


def _raster_overlay(gdf, column: str, vmax: float, res: float = 0.01):
    """Rasterise cell values to an RGBA PNG data URI for an ImageOverlay."""
    import base64
    import io

    import matplotlib
    import numpy as np
    from PIL import Image
    from rasterio.features import rasterize
    from rasterio.transform import from_origin

    minx, miny, maxx, maxy = gdf.total_bounds
    width = int(np.ceil((maxx - minx) / res))
    height = int(np.ceil((maxy - miny) / res))
    transform = from_origin(minx, maxy, res, res)
    arr = rasterize(
        ((geom, val) for geom, val in zip(gdf.geometry, gdf[column])),
        out_shape=(height, width), transform=transform, fill=np.nan, dtype="float32",
    )
    rgba = matplotlib.colormaps["YlOrRd"](np.clip(arr / vmax, 0, 1))
    rgba[..., 3] = np.where(np.isnan(arr), 0, 1)
    img = Image.fromarray((rgba * 255).astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return uri, [[miny, minx], [maxy, maxx]]


def build_interactive_map() -> None:
    aoi = load_districts()
    grid = build_grid(aoi)[["cell_id", "district", "geometry"]]
    center = [aoi.geometry.centroid.y.mean(), aoi.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron", control_scale=True)

    folium.GeoJson(
        aoi[["district", "geometry"]].to_json(), name="Districts",
        style_function=lambda _: {"color": "#333333", "weight": 1.4, "fill": False},
        tooltip=folium.GeoJsonTooltip(fields=["district"], aliases=["District"]),
    ).add_to(m)

    # Observed fire, one layer per season
    fire_max = 1.0
    per_year = {}
    for y in STUDY_YEARS:
        f = fetch_firms(y).groupby("cell_id", as_index=False)["n_fire_px"].sum()
        per_year[y] = f
        if len(f):
            fire_max = max(fire_max, float(f["n_fire_px"].quantile(0.98)))
    fire_cmap = cm.linear.OrRd_09.scale(0, fire_max)
    fire_cmap.caption = "Observed MODIS fire pixel-months per 3 km cell"
    for y in STUDY_YEARS:
        gdf = grid.merge(per_year[y], on="cell_id", how="inner")
        if gdf.empty:
            continue
        folium.GeoJson(
            _geojson(gdf, ["district", "n_fire_px"]), name=f"Observed fire {y}", show=(y == STUDY_YEARS[0]),
            style_function=lambda feat: {"fillColor": fire_cmap(min(feat["properties"]["n_fire_px"], fire_max)),
                                         "color": None, "weight": 0, "fillOpacity": 0.8},
            tooltip=folium.GeoJsonTooltip(fields=["district", "n_fire_px"],
                                          aliases=["District", "Fire pixel-months"]),
        ).add_to(m)
    fire_cmap.add_to(m)

    # Modelled susceptibility, mean over the dry-season months, per season.
    # Drawn as a raster overlay rather than 8,000 polygons per season, which
    # keeps the page light; hover values are on the observed-fire layers.
    sp = DATA_PROCESSED / "susceptibility_scores.parquet"
    if sp.exists():
        s = pd.read_parquet(sp)
        agg = s.groupby(["year", "cell_id"], as_index=False)["susceptibility"].mean()
        hi = float(agg["susceptibility"].quantile(0.98)) or 1.0
        sus_cmap = cm.linear.YlOrRd_09.scale(0, hi)
        sus_cmap.caption = "Modelled monthly fire probability, dry-season mean"
        for y in STUDY_YEARS:
            gdf = grid.merge(agg[agg["year"] == y], on="cell_id", how="inner")
            png, bounds = _raster_overlay(gdf, "susceptibility", hi)
            folium.raster_layers.ImageOverlay(
                image=png, bounds=bounds, name=f"Susceptibility {y}", show=False, opacity=0.75,
                interactive=False, cross_origin=False,
            ).add_to(m)
        sus_cmap.add_to(m)

    # Peat extent
    pp = DATA_PROCESSED / "feature_table.parquet"
    if pp.exists():
        peat = (pd.read_parquet(pp, columns=["cell_id", "peat_share"])
                .drop_duplicates("cell_id"))
        gdf = grid.merge(peat[peat["peat_share"] >= 0.5], on="cell_id", how="inner")
        gdf["peat_share"] = gdf["peat_share"].round(2)
        folium.GeoJson(
            _geojson(gdf, ["peat_share"]), name="Peat, at least half the cell (PEATGRIDS)", show=False,
            style_function=lambda _: {"fillColor": "#6D4C41", "color": None, "weight": 0, "fillOpacity": 0.45},
            tooltip=folium.GeoJsonTooltip(fields=["peat_share"], aliases=["Peat share of cell"]),
        ).add_to(m)

    # Priority hotspots
    hp = DATA_PROCESSED / "emerging_hotspots.parquet"
    if hp.exists():
        cat = pd.read_parquet(hp)
        gdf = grid.merge(cat[["cell_id", "category"]], on="cell_id", how="inner")
        gdf = gdf[gdf["category"].isin(["persistent", "intensifying", "new"])]
        colors = {"persistent": "#7a0177", "intensifying": "#c51b8a", "new": "#fa9fb5"}
        if len(gdf):
            folium.GeoJson(
                _geojson(gdf, ["district", "category"]), name="Priority hotspots", show=False,
                style_function=lambda feat: {"fillColor": colors.get(feat["properties"]["category"], "#999"),
                                             "color": None, "weight": 0, "fillOpacity": 0.8},
                tooltip=folium.GeoJsonTooltip(fields=["district", "category"], aliases=["District", "Category"]),
            ).add_to(m)

    # Smoke-direction proxy
    tp = DATA_PROCESSED / "smoke_trajectories.parquet"
    if tp.exists():
        traj = pd.read_parquet(tp)
        for y in STUDY_YEARS:
            fg = folium.FeatureGroup(name=f"Smoke direction proxy {y}", show=False)
            for _, r in traj[traj["year"] == y].iterrows():
                folium.PolyLine(
                    [(r["start_lat"], r["start_lon"]), (r["end_lat"], r["end_lon"])],
                    color="#D32F2F", weight=3,
                    tooltip=f"{r['district']}: bearing {r['bearing_deg']} degrees, {r['dist_km_24h']} km per 24 h",
                ).add_to(fg)
            fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    OUT_INTERACTIVE.mkdir(parents=True, exist_ok=True)
    out = OUT_INTERACTIVE / "peatfire_explorer.html"
    m.save(str(out))
    log_step(f"interactive map saved: {out.name} ({out.stat().st_size / 1e6:.1f} MB)", "OK")
