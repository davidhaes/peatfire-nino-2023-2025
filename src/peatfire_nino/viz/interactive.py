from __future__ import annotations

import branca.colormap as cm
import folium
import geopandas as gpd
import pandas as pd

from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_INTERACTIVE


def build_interactive_map() -> None:
    """Assemble all layers into one HTML with layer control."""
    aoi = load_districts()
    grid = build_grid(aoi)
    center = [aoi.geometry.centroid.y.mean(), aoi.geometry.centroid.x.mean()]

    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron",
                   control_scale=True)

    # districts
    folium.GeoJson(
        aoi.to_json(), name="Districts",
        style_function=lambda _: {"color": "#333333", "weight": 1.2, "fill": False},
    ).add_to(m)

    # susceptibility choropleth (2023, peat cells)
    sp = DATA_PROCESSED / "susceptibility_scores.parquet"
    if sp.exists():
        s = pd.read_parquet(sp)
        s = s[(s["year"] == 2023) & (s["peat_likely"] == 1)]
        gdf = grid.merge(s[["cell_id", "susceptibility"]], on="cell_id", how="inner")
        cmap = cm.linear.YlOrRd_09.scale(0, 1)
        cmap.caption = "Fire susceptibility (2023)"

        def _style(feat):
            v = feat["properties"]["susceptibility"]
            return {"fillColor": cmap(v), "color": cmap(v),
                    "weight": 0, "fillOpacity": 0.7}

        folium.GeoJson(
            gdf[["susceptibility", "geometry"]].to_json(), name="Susceptibility 2023",
            style_function=_style,
            tooltip=folium.GeoJsonTooltip(fields=["susceptibility"],
                                          aliases=["Susceptibility"]),
        ).add_to(m)
        cmap.add_to(m)

    # priority hotspots
    hp = DATA_PROCESSED / "emerging_hotspots.parquet"
    if hp.exists():
        cat = pd.read_parquet(hp)
        gdf = grid.merge(cat[["cell_id", "category"]], on="cell_id", how="inner")
        gdf = gdf[gdf["category"].isin(["persistent", "intensifying", "new"])]
        colors = {"persistent": "#7a0177", "intensifying": "#c51b8a", "new": "#fa9fb5"}
        fg = folium.FeatureGroup(name="Priority hotspots")
        for _, r in gdf.iterrows():
            folium.GeoJson(
                gpd.GeoSeries([r.geometry]).to_json(),
                style_function=lambda _f, c=colors.get(r["category"], "#999"):
                    {"fillColor": c, "color": c, "weight": 0, "fillOpacity": 0.8},
                tooltip=r["category"],
            ).add_to(fg)
        fg.add_to(m)

    # smoke export arrows (2023)
    tp = DATA_PROCESSED / "smoke_trajectories.parquet"
    if tp.exists():
        traj = pd.read_parquet(tp)
        fg = folium.FeatureGroup(name="Smoke export (proxy, 2023)")
        for _, r in traj[traj["year"] == 2023].iterrows():
            folium.PolyLine(
                [(r["start_lat"], r["start_lon"]), (r["end_lat"], r["end_lon"])],
                color="#D32F2F", weight=2.5,
                tooltip=f"{r['district']} bearing {r['bearing_deg']} deg",
            ).add_to(fg)
        fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    OUT_INTERACTIVE.mkdir(parents=True, exist_ok=True)
    out = OUT_INTERACTIVE / "peatfire_explorer.html"
    m.save(str(out))
    log_step(f"interactive map saved: {out.name}", "OK")
