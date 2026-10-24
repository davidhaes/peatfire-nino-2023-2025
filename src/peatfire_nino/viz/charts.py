"""charts.py
Publication-grade charts with professional labels and an abbreviation glossary.
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import pandas as pd

from peatfire_nino.config import STUDY_YEARS
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, DATA_RAW, OUT_FIGURES, OUT_TABLES
from peatfire_nino.viz.style import DPI, GLOSSARY, pretty


def _foot(fig) -> None:
    fig.text(0.01, 0.005, GLOSSARY, fontsize=7, color="#777", ha="left", style="italic")


def _shap_global() -> None:
    p = OUT_TABLES / "shap_global_importance.csv"
    if not p.exists():
        return
    s = pd.read_csv(p, index_col=0).iloc[:, 0].sort_values()
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    bars = ax.barh([pretty(i) for i in s.index], s.values, color="#B30000")
    ax.set_xlabel("Mean |SHAP|, log-odds of monthly fire")
    ax.set_title("Global Driver Importance", fontweight="bold", loc="left", fontsize=13)
    vmax = float(s.values.max())
    ax.set_xlim(0, vmax * 1.15)
    for b, v in zip(bars, s.values):
        ax.text(v + vmax * 0.01, b.get_y() + b.get_height() / 2, f"{v:.3f}",
                va="center", ha="left", fontsize=8, color="#333")
    fig.tight_layout(rect=[0, 0.04, 1, 1]); _foot(fig)
    fig.savefig(OUT_FIGURES / "chart_shap_global.png", dpi=DPI); plt.close(fig)


def _shap_heatmap() -> None:
    p = OUT_TABLES / "shap_attribution.json"
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    per, feats = d["per_district"], d["global_ranking"]
    mat = pd.DataFrame({k: [v["mean_abs_shap"].get(f, 0.0) for f in feats]
                        for k, v in per.items()}, index=[pretty(f) for f in feats])
    fig, ax = plt.subplots(figsize=(9, 6.5))
    im = ax.imshow(mat.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(mat.shape[1])); ax.set_xticklabels(mat.columns, rotation=30, ha="right", fontsize=8.5)
    ax.set_yticks(range(mat.shape[0])); ax.set_yticklabels(mat.index, fontsize=8.5)
    vmax = mat.values.max()
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat.values[i, j]
            ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=7,
                    color="white" if v > vmax * 0.55 else "#222")
    ax.set_title("Driver Importance by District (mean |SHAP|)", fontweight="bold", loc="left", fontsize=13)
    fig.colorbar(im, ax=ax, label="mean |SHAP|, log-odds", fraction=0.046, pad=0.02)
    fig.tight_layout(rect=[0, 0.04, 1, 1]); _foot(fig)
    fig.savefig(OUT_FIGURES / "chart_shap_by_district.png", dpi=DPI); plt.close(fig)


def _windrose() -> None:
    try:
        from windrose import WindroseAxes
    except Exception as exc:
        log_step(f"windrose unavailable: {exc}", "WARN"); return
    p = OUT_TABLES / "smoke_export_bearing.csv"
    if not p.exists():
        return
    df = pd.read_csv(p)
    fig = plt.figure(figsize=(6.5, 6.5))
    wa = WindroseAxes(fig, [0.1, 0.1, 0.8, 0.8]); fig.add_axes(wa)
    wa.bar(df["export_bearing_deg"], df["mean_wind_ms"], normed=True, opening=0.8,
           edgecolor="white", cmap=plt.cm.magma)
    wa.set_legend(title="Wind speed (m/s)", loc="lower left", fontsize=7)
    wa.set_title("Smoke Export Bearing on High Activity Days", fontweight="bold")
    fig.savefig(OUT_FIGURES / "chart_windrose.png", dpi=DPI, bbox_inches="tight"); plt.close(fig)


def _year_comparison() -> None:
    sp = DATA_PROCESSED / "susceptibility_scores.parquet"
    if not sp.exists():
        return
    s = pd.read_parquet(sp); peat = s[s["peat_likely"] == 1]
    rate = peat.groupby("year")["fire"].mean()
    ep = DATA_RAW / "burned_area_mcd64a1.csv"; burned = None
    if ep.exists():
        e = pd.read_csv(ep)
        if not e.empty:
            burned = e.groupby("year")["burned_area_ha"].sum().reindex(list(STUDY_YEARS), fill_value=0)
    years = [str(y) for y in STUDY_YEARS]
    fig, ax1 = plt.subplots(figsize=(7.5, 5))
    ax1.bar(years, [rate.get(y, 0) for y in STUDY_YEARS], color="#D7301F", alpha=0.85,
            label="Fire rate (peat cells)")
    ax1.set_ylabel("Fire-positive cell rate", color="#D7301F"); ax1.set_xlabel("Year")
    ax1.set_title("Fire Rate on Peat and Burned Area by Year",
                  fontweight="bold", loc="left", fontsize=13)
    if burned is not None:
        ax2 = ax1.twinx()
        ax2.plot(years, [burned.get(y, 0) for y in STUDY_YEARS], "o-", color="#1a1a1a", lw=2,
                 label="Burned area (ha)")
        ax2.set_ylabel("Burned area (ha, MODIS MCD64A1)", color="#1a1a1a")
        h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_FIGURES / "chart_year_comparison.png", dpi=DPI); plt.close(fig)


def _spacetime() -> None:
    gp = DATA_PROCESSED / "gistar_spacetime.parquet"
    if not gp.exists():
        return
    gi = pd.read_parquet(gp).set_index("cell_id")
    hot = (gi > 1.96).mean(axis=0)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(hot.index, hot.values, "o-", color="#B30000", lw=2)
    ax.set_ylabel("Share of cells in hot cluster\n(Getis-Ord Gi* z > 1.96)")
    ax.set_xlabel("Time bin (year-month)")
    ax.set_title("Temporal Evolution of Fire Hot Clusters", fontweight="bold", loc="left", fontsize=13)
    plt.xticks(rotation=45, ha="right", fontsize=8); fig.tight_layout()
    fig.savefig(OUT_FIGURES / "chart_spacetime_hotshare.png", dpi=DPI); plt.close(fig)


def _interactions() -> None:
    p = OUT_TABLES / "shap_interactions.json"
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8")); pairs = d.get("top_interactions", [])
    if not pairs:
        return
    labels = [f"{pretty(x['feature_a'])}  x  {pretty(x['feature_b'])}" for x in pairs]
    vals = [x["interaction_strength"] for x in pairs]
    fig, ax = plt.subplots(figsize=(9.5, 5))
    vv = vals[::-1]
    bars = ax.barh(labels[::-1], vv, color="#6A1B9A")
    ax.set_xlabel("Mean |SHAP interaction value| (log-odds)")
    ax.set_title("Strongest Driver Interactions", fontweight="bold", loc="left", fontsize=13)
    vmax = max(vv)
    ax.set_xlim(0, vmax * 1.18)
    for b, v in zip(bars, vv):
        ax.text(v + vmax * 0.012, b.get_y() + b.get_height() / 2, f"{v:.4f}",
                va="center", ha="left", fontsize=8.5, color="#333")
    fig.tight_layout(rect=[0, 0.05, 1, 1]); _foot(fig)
    fig.savefig(OUT_FIGURES / "chart_interactions.png", dpi=DPI); plt.close(fig)


def _pdp() -> None:
    p = OUT_TABLES / "shap_interactions.json"
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8")); pdp = d.get("partial_dependence", {})
    feats = list(pdp.keys())
    if not feats:
        return
    fig, axes = plt.subplots(1, len(feats), figsize=(4 * len(feats), 4))
    if len(feats) == 1:
        axes = [axes]
    for ax, f in zip(axes, feats):
        xs = [c["bin_center"] for c in pdp[f]]; ys = [c["mean_fire_prob"] for c in pdp[f]]
        ax.plot(xs, ys, "o-", color="#B30000", lw=2)
        ax.set_xlabel(pretty(f)); ax.set_ylabel("Mean predicted monthly fire probability")
        ax.set_title(pretty(f), fontsize=11, fontweight="bold"); ax.grid(alpha=0.3)
    fig.suptitle("Partial Dependence on the Four Strongest Drivers", fontweight="bold", fontsize=13)
    fig.tight_layout(rect=[0, 0.05, 1, 0.96]); _foot(fig)
    fig.savefig(OUT_FIGURES / "chart_partial_dependence.png", dpi=DPI); plt.close(fig)


def _carbon() -> None:
    import json as _json
    p = OUT_TABLES / "carbon_emissions.json"
    if not p.exists():
        return
    d = _json.loads(p.read_text(encoding="utf-8"))
    byd = d.get("by_district", [])
    byy = d.get("by_year", [])
    rng = d.get("co2_estimate_range_Mt", {})
    if not byd:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2))
    fig.subplots_adjust(top=0.80, bottom=0.12, left=0.13, right=0.97, wspace=0.28)

    byd_sorted = sorted(byd, key=lambda r: -(r.get("co2_high_t", 0)))
    names = [r["district"] for r in byd_sorted]
    low = [r.get("co2_low_t", 0) / 1e6 for r in byd_sorted]
    high = [r.get("co2_high_t", 0) / 1e6 for r in byd_sorted]
    mid = [(l + h) / 2 for l, h in zip(low, high)]
    err = [[m - l for m, l in zip(mid, low)], [h - m for h, m in zip(high, mid)]]
    yy = list(range(len(names)))[::-1]
    ax1.barh(yy, mid, xerr=err, color="#8B4513", alpha=0.85, capsize=5,
             error_kw={"ecolor": "#444", "lw": 1.3}, height=0.6)
    ax1.set_yticks(yy); ax1.set_yticklabels(names, fontsize=10)
    ax1.set_xlabel("Estimated CO2 emission (million tonnes)", fontsize=10)
    ax1.set_title("Carbon Emission by District", fontweight="bold", loc="left", fontsize=13, pad=10)
    xmax = max(high) if high else 1
    ax1.set_xlim(0, xmax * 1.25)
    for yi, (mv, h) in zip(yy, zip(mid, high)):
        ax1.text(h + xmax * 0.02, yi, f"{mv:.1f} Mt", va="center", ha="left",
                 fontsize=9, color="#222", fontweight="bold")
    ax1.grid(axis="x", alpha=0.25); ax1.set_axisbelow(True)

    years = [str(r["year"]) for r in byy]
    ha = [r.get("burned_ha", 0) for r in byy]
    ha_peat = [r.get("burned_peat_ha", 0) for r in byy]
    bars = ax2.bar(years, ha, color="#E8B48A", alpha=0.9, width=0.6, label="All burned area")
    ax2.bar(years, ha_peat, color="#8B4513", alpha=0.9, width=0.6, label="On peat (PEATGRIDS)")
    ax2.legend(fontsize=8, loc="upper right")
    ax2.set_ylabel("Burned area (hectares, MODIS MCD64A1)", fontsize=10)
    ax2.set_xlabel("Year", fontsize=10)
    ax2.set_title("Burned Area by Year", fontweight="bold", loc="left", fontsize=13, pad=10)
    ax2.set_ylim(0, (max(ha) if ha else 1) * 1.18)
    for b, v in zip(bars, ha):
        ax2.text(b.get_x() + b.get_width() / 2, v + (max(ha) if ha else 1) * 0.015,
                 f"{v:,.0f} ha", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax2.grid(axis="y", alpha=0.25); ax2.set_axisbelow(True)

    yrs = d.get("years") or [int(y) for y in years]
    span = f"{min(yrs)} to {max(yrs)}" if yrs else ""
    total_ha = sum(r.get("burned_ha", 0) for r in byd) or 1.0
    top = max(byd, key=lambda r: r.get("burned_ha", 0))
    top_share = 100.0 * top.get("burned_ha", 0) / total_ha
    top_year = max(byy, key=lambda r: r.get("burned_ha", 0)) if byy else None
    fig.text(0.5, 0.95,
             f"Indicative CO2 from Burned Peat: {rng.get('low','?')} to {rng.get('high','?')} Mt, {span}",
             ha="center", fontweight="bold", fontsize=14)
    fig.text(0.5, 0.895,
             (f"{top_year['year']} holds the most burned area; " if top_year else "")
             + f"{top['district']} accounts for {top_share:.0f} percent of all burned area",
             ha="center", fontsize=9.5, color="#555")
    fig.text(0.01, 0.02,
             "Peat fuel applied to burned area on peat only. Order of magnitude from MODIS MCD64A1 and "
             "literature fuel and emission-factor ranges.",
             fontsize=7.5, color="#888", style="italic")
    fig.savefig(OUT_FIGURES / "chart_carbon_emissions.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def render_charts() -> None:
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    for fn in (_shap_global, _shap_heatmap, _windrose, _year_comparison,
               _spacetime, _interactions, _pdp, _carbon):
        try:
            fn()
        except Exception as exc:
            log_step(f"chart {fn.__name__} failed: {exc}", "WARN")
    log_step("charts rendered", "OK")
