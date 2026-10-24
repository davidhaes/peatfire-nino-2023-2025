"""maps_static.py
Publication-grade static maps: shaded-relief basemap, offset district labels,
lower-left legends, tight framing, clean titles. Built to publish.
"""
from __future__ import annotations

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_FIGURES
from peatfire_nino.viz.style import (BOUNDARY, BW, DPI, HALO, LABEL_OFFSET, SRC,
                                     basemap_provider)


def _basemap(ax) -> None:
    try:
        import contextily as cx
        cx.add_basemap(ax, source=basemap_provider(), crs="EPSG:4326", attribution=False)
    except Exception as exc:
        log_step(f"basemap skipped: {exc}", "WARN")


def _frame(ax, gdf, pad=0.08) -> None:
    minx, miny, maxx, maxy = gdf.total_bounds
    dx, dy = (maxx - minx), (maxy - miny)
    ax.set_xlim(minx - dx * pad, maxx + dx * pad)
    ax.set_ylim(miny - dy * pad, maxy + dy * pad)


def _north(ax, x=0.965, y=0.94) -> None:
    ax.annotate("N", xy=(x, y), xytext=(x, y - 0.065),
                arrowprops=dict(facecolor="#000", width=3, headwidth=9),
                ha="center", va="center", fontsize=10, fontweight="bold",
                xycoords="axes fraction")


def _labels(ax, aoi) -> None:
    for _, r in aoi.iterrows():
        c = r.geometry.representative_point()
        dx, dy = LABEL_OFFSET.get(r["district"], (0.0, 0.5))
        ax.text(c.x + dx, c.y + dy, r["district"], fontsize=8.5, fontweight="bold",
                color="#1a1a1a", ha="center", va="center", path_effects=HALO)


def _finalize(ax, title, subtitle) -> None:
    ax.set_title(title, fontsize=15, fontweight="bold", loc="left", pad=24, color="#1a1a1a")
    ax.text(0.0, 1.012, subtitle, transform=ax.transAxes, fontsize=9.5,
            color="#555", va="bottom", ha="left")
    ax.text(0.0, -0.03, SRC, transform=ax.transAxes, fontsize=7.5,
            color="#888", va="top", ha="left", style="italic")
    ax.set_axis_off()


def _overview() -> None:
    aoi = load_districts()
    fires = pd.concat([fetch_firms(y) for y in (2023, 2024, 2025)], ignore_index=True)
    per_cell = fires.groupby("cell_id", as_index=False)["n_fire_px"].sum()
    grid = build_grid(aoi)
    burning = grid.merge(per_cell, on="cell_id", how="inner")
    fig, ax = plt.subplots(figsize=(12, 7))
    aoi.plot(ax=ax, facecolor="#ffffff", edgecolor=BOUNDARY, linewidth=BW, alpha=0.3)
    burning.plot(ax=ax, column="n_fire_px", cmap="YlOrRd", linewidth=0, alpha=0.9,
                 legend=True, legend_kwds={"label": "Fire pixel-months per 3 km cell", "shrink": 0.6})
    _basemap(ax); _frame(ax, aoi); _labels(ax, aoi); _north(ax)
    _finalize(ax, "Study Area and Active Fire",
              "MODIS active fire (FIRMS, 1 km), 2023 to 2025 dry season (June to November)")
    fig.savefig(OUT_FIGURES / "01_overview.png", dpi=DPI, bbox_inches="tight"); plt.close(fig)


def _susceptibility() -> None:
    scores = pd.read_parquet(DATA_PROCESSED / "susceptibility_scores.parquet")
    grid = build_grid(load_districts())
    s = scores[(scores["year"] == 2023) & (scores["peat_likely"] == 1)]
    s = s.groupby("cell_id", as_index=False)["susceptibility"].mean()
    gdf = grid.merge(s, on="cell_id", how="inner"); aoi = load_districts()
    fig, ax = plt.subplots(figsize=(12, 7))
    gdf.plot(ax=ax, column="susceptibility", cmap="YlOrRd", scheme="quantiles", k=5, alpha=0.9,
             legend=True, legend_kwds={"title": "Fire susceptibility\n(probability)",
                          "loc": "lower left", "fontsize": 8.5, "title_fontsize": 9.5,
                          "framealpha": 0.92, "edgecolor": "#ccc"})
    aoi.plot(ax=ax, facecolor="none", edgecolor=BOUNDARY, linewidth=BW)
    _basemap(ax); _frame(ax, gdf); _labels(ax, aoi); _north(ax)
    _finalize(ax, "Peatland Fire Susceptibility, 2023 El Nino Peak",
              "LightGBM monthly fire probability, dry season mean, cells at least half PEATGRIDS peat")
    fig.savefig(OUT_FIGURES / "02_susceptibility.png", dpi=DPI, bbox_inches="tight"); plt.close(fig)


def _hotspots() -> None:
    cat = pd.read_parquet(DATA_PROCESSED / "emerging_hotspots.parquet")
    grid = build_grid(load_districts())
    gdf = grid.merge(cat[["cell_id", "category"]], on="cell_id", how="inner"); aoi = load_districts()
    cmap = {"new": "#D32F2F", "intensifying": "#1565C0", "persistent": "#6A1B9A", "diminishing": "#9E9E9E"}
    fig, ax = plt.subplots(figsize=(12, 7))
    gdf.plot(ax=ax, color="#dddddd", alpha=0.4)
    present = []
    for lab, col in cmap.items():
        sub = gdf[gdf["category"] == lab]
        if not sub.empty:
            sub.plot(ax=ax, color=col, alpha=0.95); present.append((lab, col, len(sub)))
    aoi.plot(ax=ax, facecolor="none", edgecolor=BOUNDARY, linewidth=BW)
    handles = [mpatches.Patch(color=c, label=f"{lab} (n={n})") for lab, c, n in present]
    ax.legend(handles=handles, title="Emerging hotspot class", loc="lower left",
              fontsize=8.5, title_fontsize=9.5, framealpha=0.92, edgecolor="#ccc")
    _basemap(ax); _frame(ax, gdf); _labels(ax, aoi); _north(ax)
    _finalize(ax, "Priority Emerging Fire Hotspots",
              "Getis-Ord Gi* per month with Mann-Kendall trend, 2023 to 2025")
    fig.savefig(OUT_FIGURES / "03_priority_hotspots.png", dpi=DPI, bbox_inches="tight"); plt.close(fig)


def _smoke() -> None:
    tp = DATA_PROCESSED / "smoke_trajectories.parquet"
    if not tp.exists():
        return
    traj = pd.read_parquet(tp); aoi = load_districts()
    fig, ax = plt.subplots(figsize=(12, 7))
    aoi.plot(ax=ax, facecolor="#ffffff", edgecolor=BOUNDARY, linewidth=BW, alpha=0.3)
    for _, r in traj[traj["year"] == 2023].iterrows():
        ax.annotate("", xy=(r["end_lon"], r["end_lat"]), xytext=(r["start_lon"], r["start_lat"]),
                    arrowprops=dict(arrowstyle="-|>", color="#D32F2F", lw=2.6))
    _basemap(ax); _frame(ax, aoi); _labels(ax, aoi); _north(ax)
    _finalize(ax, "Dominant Smoke Export Direction (Proxy)",
              "Fire-weighted ERA5-Land wind on high-activity days, 24 hour straight line, 2023")
    fig.savefig(OUT_FIGURES / "04_smoke_export.png", dpi=DPI, bbox_inches="tight"); plt.close(fig)


def _year_delta() -> None:
    scores = pd.read_parquet(DATA_PROCESSED / "susceptibility_scores.parquet")
    grid = build_grid(load_districts())
    s = scores[scores["peat_likely"] == 1]
    piv = (s.groupby(["cell_id", "year"], as_index=False)["susceptibility"].mean()
           .pivot_table(index="cell_id", columns="year", values="susceptibility"))
    if not {2023, 2024}.issubset(piv.columns):
        return
    piv["delta"] = piv[2023] - piv[2024]
    gdf = grid.merge(piv["delta"].reset_index(), on="cell_id", how="inner"); aoi = load_districts()
    vmax = float(np.nanpercentile(np.abs(gdf["delta"]), 98)) or 0.1
    fig, ax = plt.subplots(figsize=(12, 7))
    cax = ax.inset_axes([0.66, 0.06, 0.30, 0.022])
    gdf.plot(ax=ax, column="delta", cmap="RdBu_r", vmin=-vmax, vmax=vmax, alpha=0.9,
             legend=True, cax=cax, legend_kwds={"orientation": "horizontal"})
    cax.set_title("Higher in 2023 (red)  vs  2024 (blue)", fontsize=7.5, color="#333")
    cax.tick_params(labelsize=7)
    aoi.plot(ax=ax, facecolor="none", edgecolor=BOUNDARY, linewidth=BW)
    _basemap(ax); _frame(ax, gdf); _labels(ax, aoi); _north(ax)
    _finalize(ax, "Modelled Fire Susceptibility, 2023 minus 2024",
              "Dry-season mean monthly probability; red is higher in the 2023 El Nino season, blue higher in 2024")
    fig.savefig(OUT_FIGURES / "05_year_delta.png", dpi=DPI, bbox_inches="tight"); plt.close(fig)


def _yearly_panels() -> None:
    """Clean table layout: rows = districts, columns = years. Uniform cells, framed."""
    scores = pd.read_parquet(DATA_PROCESSED / "susceptibility_scores.parquet")
    grid = build_grid(load_districts())
    aoi = load_districts()
    years = [y for y in (2023, 2024, 2025) if y in scores["year"].unique()]
    districts = list(aoi["district"])
    nrow, ncol = len(districts), len(years)
    if nrow == 0 or ncol == 0:
        return

    # uniform cell size; constrained_layout keeps the table tidy
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.9 * ncol + 1.2, 2.5 * nrow),
                             constrained_layout=False)
    fig.subplots_adjust(left=0.13, right=0.88, top=0.90, bottom=0.04,
                        wspace=0.06, hspace=0.12)
    if nrow == 1:
        axes = axes.reshape(1, -1)
    if ncol == 1:
        axes = axes.reshape(-1, 1)

    mappable = None
    for i, dist in enumerate(districts):
        drow = aoi[aoi["district"] == dist]
        dgrid = grid[grid["district"] == dist] if "district" in grid.columns else grid
        # fixed equal bounds per district row (same extent across the 3 year columns)
        minx, miny, maxx, maxy = drow.total_bounds
        dx, dy = (maxx - minx), (maxy - miny)
        pad = 0.10
        xlim = (minx - dx * pad, maxx + dx * pad)
        ylim = (miny - dy * pad, maxy + dy * pad)
        for j, yr in enumerate(years):
            ax = axes[i, j]
            s = scores[(scores["year"] == yr) & (scores["peat_likely"] == 1)]
            s = s.groupby("cell_id", as_index=False)["susceptibility"].mean()
            gdf = dgrid.merge(s, on="cell_id", how="inner")
            if not gdf.empty:
                art = gdf.plot(ax=ax, column="susceptibility", cmap="YlOrRd",
                               vmin=0, vmax=0.5, alpha=0.95)
                mappable = art.collections[-1] if art.collections else mappable
            drow.plot(ax=ax, facecolor="none", edgecolor=BOUNDARY, linewidth=0.8)
            ax.set_xlim(*xlim); ax.set_ylim(*ylim)
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_aspect("equal", adjustable="datalim")
            for spine in ax.spines.values():
                spine.set_edgecolor("#cccccc")
                spine.set_linewidth(0.8)
            if i == 0:
                ax.set_title(str(yr), fontsize=13, fontweight="bold", pad=8)
            if j == 0:
                ax.set_ylabel(dist, fontsize=10, fontweight="bold", rotation=90,
                              labelpad=10)

    fig.suptitle("Fire Susceptibility by District and Year",
                 fontsize=15, fontweight="bold", y=0.965)
    fig.text(0.5, 0.93, "Declining intensity after the 2023 El Nino peak",
             ha="center", fontsize=10, color="#555")

    # single tidy colorbar on the right, spanning the table height
    import matplotlib as mpl
    sm = mpl.cm.ScalarMappable(cmap="YlOrRd", norm=mpl.colors.Normalize(0, 0.5))
    cax = fig.add_axes([0.90, 0.15, 0.018, 0.6])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label("Fire susceptibility (probability)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    fig.text(0.13, 0.012, _src_short(), fontsize=7.5, color="#888", style="italic")
    fig.savefig(OUT_FIGURES / "06_yearly_panels.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def _src_short() -> str:
    return SRC

def render_static_maps() -> None:
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    for fn in (_overview, _susceptibility, _hotspots, _smoke, _year_delta, _yearly_panels):
        try:
            fn()
        except Exception as exc:
            log_step(f"map {fn.__name__} failed: {exc}", "WARN")
    log_step("static maps rendered", "OK")
