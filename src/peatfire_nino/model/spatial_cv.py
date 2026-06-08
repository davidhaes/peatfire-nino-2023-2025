"""spatial_cv.py
Leave-one-district-out spatial cross-validation.
Tests whether the model learns transferable mechanism vs memorising locations.
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from peatfire_nino.config import RANDOM_SEED
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_TABLES
from peatfire_nino.model.susceptibility import FEATURES, _params


def spatial_cross_validate() -> dict:
    """Leave-one-district-out CV. Each fold tests on a held-out district."""
    table = pd.read_parquet(DATA_PROCESSED / "feature_table.parquet")
    districts = sorted(table["district"].dropna().unique())

    folds = []
    for held in districts:
        train = table[table["district"] != held]
        test = table[table["district"] == held]
        if train.empty or test.empty or test["fire"].nunique() < 2:
            log_step(f"spatial fold '{held}' skipped (insufficient class variety)", "WARN")
            continue
        pos = int(train["fire"].sum())
        neg = int((train["fire"] == 0).sum())
        dtrain = lgb.Dataset(train[FEATURES], label=train["fire"])
        booster = lgb.train(_params(pos, neg), dtrain, num_boost_round=300)
        proba = booster.predict(test[FEATURES])
        folds.append({
            "held_out_district": held,
            "roc_auc": round(float(roc_auc_score(test["fire"], proba)), 3),
            "pr_auc": round(float(average_precision_score(test["fire"], proba)), 3),
            "n_test": int(len(test)),
            "n_test_fire": int(test["fire"].sum()),
        })
        log_step(f"spatial fold held={held}: ROC-AUC={folds[-1]['roc_auc']:.3f} "
                 f"PR-AUC={folds[-1]['pr_auc']:.3f}", "OK")

    if folds:
        mean_roc = float(np.mean([f["roc_auc"] for f in folds]))
        mean_pr = float(np.mean([f["pr_auc"] for f in folds]))
    else:
        mean_roc = mean_pr = float("nan")

    out = {
        "method": "leave-one-district-out spatial CV",
        "folds": folds,
        "mean_roc_auc": round(mean_roc, 3),
        "mean_pr_auc": round(mean_pr, 3),
        "interpretation": "If spatial mean ROC-AUC is close to the temporal hold-out AUC, "
                          "the model captures transferable mechanism rather than location memory. "
                          "A large drop indicates spatial overfitting.",
    }
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "spatial_cv.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"spatial CV done; mean ROC-AUC={mean_roc:.3f}", "OK")
    return out


def main() -> int:
    spatial_cross_validate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
