"""interaction.py
SHAP interaction values and partial dependence for top fire drivers.
Reveals nonlinear thresholds and predictor interactions (mechanistic insight).
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_TABLES
from peatfire_nino.model.susceptibility import FEATURES


def compute_interactions() -> dict:
    """Partial dependence and pairwise SHAP interactions for the top drivers.

    The sample is a plain random sample of the table, so it represents the
    landscape the model is applied to. The earlier version kept every fire
    row and 30,000 non-fire rows, then averaged predictions within bins of
    each driver. On a fire-enriched sample that curve is not a partial
    dependence and its levels are not fire probabilities.

    Partial dependence here is the textbook one: set a driver to a value for
    every row in the sample, predict, average. The drivers are the four with
    the largest mean absolute SHAP value, not a hard-coded list.
    """
    table = pd.read_parquet(DATA_PROCESSED / "feature_table.parquet")
    model = lgb.Booster(model_file=str(DATA_PROCESSED / "lgbm_susceptibility.txt"))

    sample = table.sample(min(20000, len(table)), random_state=42).reset_index(drop=True)
    X = sample[FEATURES]

    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    sv_arr = sv[1] if isinstance(sv, list) else sv
    importance = pd.Series(np.abs(sv_arr).mean(axis=0), index=FEATURES).sort_values(ascending=False)
    top_drivers = importance.index[:4].tolist()

    pdp = {}
    for feat in top_drivers:
        col = X[feat].dropna()
        grid = np.unique(np.quantile(col, np.linspace(0.05, 0.95, 19)))
        curve = []
        for v in grid:
            Xv = X.copy()
            Xv[feat] = v
            curve.append({
                "bin_center": float(v),
                "mean_fire_prob": float(model.predict(Xv).mean()),
                "n": int(len(Xv)),
            })
        pdp[feat] = curve

    top_idx = [FEATURES.index(f) for f in importance.index[:6]]
    small = X.sample(min(2000, len(X)), random_state=42)
    inter = explainer.shap_interaction_values(small)
    inter_arr = inter[1] if isinstance(inter, list) else inter
    mean_abs_inter = np.abs(inter_arr).mean(axis=0)  # (n_feat, n_feat)

    pairs = []
    for a in top_idx:
        for b in top_idx:
            if a < b:
                pairs.append({
                    "feature_a": FEATURES[a],
                    "feature_b": FEATURES[b],
                    "interaction_strength": float(mean_abs_inter[a, b]),
                })
    pairs.sort(key=lambda d: d["interaction_strength"], reverse=True)

    out = {
        "partial_dependence": pdp,
        "top_interactions": pairs[:6],
        "top_drivers_by_shap": top_drivers,
        "note": "Partial dependence on a random sample of cell-months: mean predicted monthly "
                "fire probability with one driver fixed at each value. Interaction strength is "
                "mean absolute SHAP interaction value, in log-odds units.",
    }
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "shap_interactions.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"interactions computed; top pair: "
             f"{pairs[0]['feature_a']} x {pairs[0]['feature_b']}", "OK")
    return out


def main() -> int:
    compute_interactions()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
