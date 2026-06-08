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
    """Compute partial dependence on top drivers + top pairwise interactions."""
    table = pd.read_parquet(DATA_PROCESSED / "feature_table.parquet")
    model = lgb.Booster(model_file=str(DATA_PROCESSED / "lgbm_susceptibility.txt"))

    # subsample for speed; keep all positives
    pos = table[table["fire"] == 1]
    neg = table[table["fire"] == 0].sample(min(30000, (table["fire"] == 0).sum()),
                                           random_state=42)
    sample = pd.concat([pos, neg]).reset_index(drop=True)
    X = sample[FEATURES]

    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    sv_arr = sv[1] if isinstance(sv, list) else sv

    # --- Partial dependence: mean predicted prob across bins of each top driver ---
    top_drivers = ["ndwi", "vpd", "soil_moisture", "lst_k"]
    pdp = {}
    for feat in top_drivers:
        if feat not in X.columns:
            continue
        vals = X[feat].to_numpy()
        proba = model.predict(X)
        bins = np.quantile(vals, np.linspace(0, 1, 11))
        bins = np.unique(bins)
        idx = np.digitize(vals, bins)
        curve = []
        for b in range(1, len(bins)):
            mask = idx == b
            if mask.sum() > 0:
                curve.append({
                    "bin_center": float((bins[b-1] + bins[b]) / 2),
                    "mean_fire_prob": float(proba[mask].mean()),
                    "n": int(mask.sum()),
                })
        pdp[feat] = curve

    # --- Pairwise interaction strength via SHAP interaction values (top 4 feats) ---
    top_idx = [FEATURES.index(f) for f in top_drivers if f in FEATURES]
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
        "note": "PDP shows how fire probability responds to each driver; "
                "interactions reveal compound dryness effects.",
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
