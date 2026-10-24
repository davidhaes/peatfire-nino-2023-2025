"""build_reports.py
Stage: write docs/conclusions.md from findings.json.

Every sentence that states a result reads it from findings.json and is
worded conditionally on it. The earlier version fell back to hard-coded
numbers (AUC 0.708, r = 0.684, interaction 0.087) when a value was missing
and asserted "compound dryness is the dominant fire trigger" and "El Nino
strongly modulates fire activity" whatever the data said.
"""
from __future__ import annotations

import json
import sys

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DOCS, OUT_INSIGHTS
from peatfire_nino.viz.style import pretty


def _load() -> dict:
    p = OUT_INSIGHTS / "findings.json"
    if not p.exists():
        raise FileNotFoundError("findings.json missing; run analysis stages first.")
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    log_step("stage build_reports started", "INFO")
    f = _load()

    m = f.get("model") or {}
    folds = sorted(m.get("folds") or [], key=lambda x: x["test_year"])
    scv = f.get("spatial_cross_validation") or {}
    dr = f.get("drivers") or {}
    gr = dr.get("global_ranking") or []
    inter = (f.get("driver_interactions") or {}).get("top_interactions") or []
    enso = f.get("enso_linkage") or {}
    yr = {r["year"]: r for r in (f.get("susceptibility_by_year") or [])}
    bd = f.get("susceptibility_by_district") or []
    hot = (f.get("emerging_hotspots") or {}).get("category_counts") or {}
    smoke = (f.get("smoke_exposure") or {}).get("records") or []
    carbon = f.get("carbon_emissions") or {}

    lines = [
        "# Conclusions",
        "",
        "> Generated from `outputs/insights/findings.json` by `scripts/build_reports.py`. "
        "Do not edit by hand.",
        "",
        "## Answers to the research questions",
        "",
    ]

    if gr:
        top3 = ", ".join(pretty(x) for x in gr[:3])
        lines.append(f"**RQ1. Drivers.** By mean absolute SHAP value the strongest predictors are {top3}.")
        if inter:
            a, b, v = inter[0]["feature_a"], inter[0]["feature_b"], inter[0]["interaction_strength"]
            lines.append(f"The strongest pairwise interaction is {pretty(a)} with {pretty(b)} "
                         f"(mean absolute SHAP interaction {v:.3f}, log-odds).")
        lines.append("")

    if hot:
        lines.append(f"**RQ2. Hotspots.** Emerging hotspot analysis classes "
                     f"{hot.get('intensifying', 0)} cells as intensifying, {hot.get('new', 0)} as new, "
                     f"{hot.get('persistent', 0)} as persistent and {hot.get('diminishing', 0)} as diminishing.")
        lines.append("")

    if yr:
        rates = ", ".join(f"{y}: {yr[y]['fire_rate']:.4f}" for y in sorted(yr))
        lines.append(f"**RQ3. El Nino.** Share of peat cell-months with MODIS fire by season: {rates}.")
        if enso:
            lines.append(f"Monthly fire pixels correlate with ONI (OISST) at r = {enso.get('pearson_r')} over "
                         f"{enso.get('n_months')} months; a season-block permutation gives p = "
                         f"{enso.get('season_permutation_p')}. With {enso.get('n_seasons')} seasons the data "
                         "are consistent with an El Nino effect but cannot establish it.")
        lines.append("")

    if smoke:
        nw = sum(1 for r in smoke if r["export_bearing_deg"] >= 270)
        lines.append(f"**RQ4. Smoke.** {nw} of {len(smoke)} district-seasons have a fire-weighted wind "
                     "bearing between west and north on high-activity days. This is a wind proxy, not a "
                     "dispersion model.")
        lines.append("")

    lines += ["## Model skill", ""]
    if folds:
        lines.append("Leave-one-year-out (trains on the other two seasons): " + "; ".join(
            f"{x['test_year']} ROC-AUC {x['roc_auc']:.2f}, PR-AUC {x['pr_auc']:.3f} against "
            f"prevalence {x.get('prevalence', float('nan')):.3f}" for x in folds) + ".")
    if scv.get("folds"):
        lines.append(f"Leave-one-district-out mean ROC-AUC {scv.get('mean_roc_auc')}: " + "; ".join(
            f"{x['held_out_district']} {x['roc_auc']:.2f}" for x in scv["folds"]) + ".")
    lines.append("")

    if bd:
        lines += ["## Districts", "",
                  f"Highest mean modelled susceptibility on peat: {bd[0]['district']} "
                  f"({bd[0]['mean_susceptibility']:.3f}, observed fire rate {bd[0]['fire_rate']:.4f}).", ""]

    rng = carbon.get("co2_estimate_range_Mt") or {}
    if rng:
        lines += ["## Carbon", "",
                  f"Burned area {carbon.get('total_burned_ha', 0):,.0f} ha over "
                  f"{', '.join(str(y) for y in carbon.get('years', []))}, of which "
                  f"{carbon.get('total_burned_peat_ha', 0):,.0f} ha on peat. Indicative CO2 from burned peat: "
                  f"{rng.get('low')} to {rng.get('high')} Mt.", ""]

    lines += ["## Limitations", ""] + [f"{i}. {n}" for i, n in enumerate(f.get("honesty_notes") or [], 1)] + [""]

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "conclusions.md").write_text("\n".join(lines), encoding="utf-8")
    log_step("docs/conclusions.md regenerated", "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
