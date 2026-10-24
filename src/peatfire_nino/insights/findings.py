"""findings.py
Assemble outputs/insights/findings.json from ALL analysis artefacts.
Every value traces to a concrete file; missing artefacts become null.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_INSIGHTS, OUT_TABLES


def _load_json(p: Path) -> dict | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _honesty_notes(model_metrics, spatial_cv, moran, enso) -> list[str]:
    """Limitations written from the numbers, so they cannot drift from them."""
    notes = [
        "Fire labels are MODIS active fire pixels (FIRMS in Earth Engine, 1 km, confidence >= 30). "
        "Small and short fires below MODIS detection are missed.",
        "Peat extent is PEATGRIDS thickness >= 50 cm at 1 km, a modelled map rather than a survey.",
        "Surface state (NDWI, LST, soil moisture) enters from the previous month, because the "
        "same month's values are altered by the fire itself.",
        "Smoke direction is a fire-weighted ERA5-Land wind proxy, not a dispersion model.",
        "Carbon is an order-of-magnitude range for burned peat only; fuel and emission factors "
        "come from literature ranges.",
    ]
    folds = (model_metrics or {}).get("folds") or []
    aucs = [f.get("roc_auc") for f in folds if f.get("roc_auc") == f.get("roc_auc")]
    if aucs:
        notes.append(f"Leave-one-year-out ROC-AUC ranges {min(aucs):.2f} to {max(aucs):.2f}; each "
                     "fold trains on the other two seasons, including later ones, so this is not a forecast test.")
    sfolds = (spatial_cv or {}).get("folds") or []
    if sfolds:
        worst = min(sfolds, key=lambda f: f["roc_auc"])
        notes.append(f"Leave-one-district-out mean ROC-AUC {spatial_cv.get('mean_roc_auc')}; the weakest "
                     f"district is {worst['held_out_district']} at {worst['roc_auc']}.")
    if moran and moran.get("morans_I") is not None:
        notes.append(f"Residual Moran's I = {moran.get('morans_I')} (p = {moran.get('p_value')}): spatial "
                     "structure the predictors do not capture remains.")
    if enso:
        notes.append(f"ENSO: Pearson r = {enso.get('pearson_r')} over {enso.get('n_months')} months from "
                     f"{enso.get('n_seasons')} seasons; season-block permutation p = "
                     f"{enso.get('season_permutation_p')}. Three seasons cannot establish ENSO as the cause.")
    return notes


def build_findings() -> dict:
    model_metrics = _load_json(OUT_TABLES / "model_metrics.json")
    shap = _load_json(OUT_TABLES / "shap_attribution.json")
    hotspot = _load_json(OUT_TABLES / "hotspot_summary.json")
    smoke = _load_json(OUT_TABLES / "smoke_summary.json")
    interactions = _load_json(OUT_TABLES / "shap_interactions.json")
    spatial_cv = _load_json(OUT_TABLES / "spatial_cv.json")
    enso = _load_json(OUT_TABLES / "enso_linkage.json")
    carbon = _load_json(OUT_TABLES / "carbon_emissions.json")
    moran = _load_json(OUT_TABLES / "residual_moran.json")

    scores_path = DATA_PROCESSED / "susceptibility_scores.parquet"
    yearly = by_district = None
    if scores_path.exists():
        s = pd.read_parquet(scores_path)
        peat = s[s["peat_likely"] == 1] if "peat_likely" in s.columns else s
        yearly = (peat.groupby("year")
                  .agg(mean_susceptibility=("susceptibility", "mean"),
                       fire_rate=("fire", "mean"),
                       n_cells=("cell_id", "size")).round(4)
                  .reset_index().to_dict(orient="records"))
        by_district = (peat.groupby("district")
                       .agg(mean_susceptibility=("susceptibility", "mean"),
                            fire_rate=("fire", "mean")).round(4)
                       .sort_values("mean_susceptibility", ascending=False)
                       .reset_index().to_dict(orient="records"))

    if shap:
        shap = {k: v for k, v in shap.items() if not k.startswith("_")}
    if interactions:
        interactions = {k: v for k, v in interactions.items() if k != "partial_dependence"
                        or True}  # keep PDP; it is serialisable

    findings = {
        "study": "Peatland fire susceptibility, drivers, ENSO linkage, and smoke exposure 2023-2025",
        "model": model_metrics,
        "spatial_cross_validation": spatial_cv,
        "drivers": shap,
        "driver_interactions": interactions,
        "enso_linkage": enso,
        "susceptibility_by_year": yearly,
        "susceptibility_by_district": by_district,
        "emerging_hotspots": hotspot,
        "smoke_exposure": smoke,
        "carbon_emissions": carbon,
        "residual_spatial_autocorrelation": moran,
        "honesty_notes": _honesty_notes(model_metrics, spatial_cv, moran, enso),
    }
    OUT_INSIGHTS.mkdir(parents=True, exist_ok=True)
    (OUT_INSIGHTS / "findings.json").write_text(
        json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    log_step("findings.json rebuilt with all B-series analyses", "OK")
    return findings
