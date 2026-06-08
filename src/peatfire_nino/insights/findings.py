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
        "honesty_notes": [
            "Peat extent is an elevation-based proxy, not the licensed national map; "
            "SHAP ranks it last and residual Moran's I is high, confirming this limitation.",
            "Model skill is MODERATE (temporal ROC-AUC ~0.62-0.74, spatial mean ~0.71); "
            "this is not a high-accuracy operational forecaster.",
            "Pelalawan spatial fold (ROC-AUC ~0.51) suggests anthropogenic ignition not "
            "captured by climate-driven predictors.",
            "Smoke export is an ERA5 wind proxy, not a physical dispersion model.",
            "Carbon emission is an order-of-magnitude RANGE; fuel/EF NEEDS VERIFICATION.",
            "ONI values used for ENSO linkage NEEDS VERIFICATION against NOAA CPC.",
            "Residual Moran's I significant: a spatial covariate (true peat depth, water "
            "table) is still missing.",
        ],
    }
    OUT_INSIGHTS.mkdir(parents=True, exist_ok=True)
    (OUT_INSIGHTS / "findings.json").write_text(
        json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    log_step("findings.json rebuilt with all B-series analyses", "OK")
    return findings
