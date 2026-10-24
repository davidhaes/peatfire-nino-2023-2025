from __future__ import annotations

import json
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from peatfire_nino.config import RANDOM_SEED
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_TABLES

# Same-month weather, previous-month surface state, static fuel and terrain.
# Same-month NDWI, LST and soil moisture are deliberately absent: they are
# changed by the fire (burn scars, smoke, heat) and would let the outcome
# explain itself.
FEATURES = ["vpd", "wind_speed", "precip_mm", "treecover", "loss_frac",
            "elevation", "slope", "peat_share", "peat_thickness_cm",
            "ndwi_lag1", "lst_lag1", "sm_lag1",
            "vpd_lag1", "precip_lag1", "precip_cum2"]


@dataclass
class FoldResult:
    train_year: int
    test_year: int
    roc_auc: float
    pr_auc: float
    n_test_pos: int
    prevalence: float


def _params(pos: int, neg: int) -> dict:
    return {
        "objective": "binary",
        "metric": ["auc", "average_precision"],
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_data_in_leaf": 50,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        # No class reweighting. Reweighting inflates every predicted value, so
        # the "probabilities" the earlier version reported (0.36 at high VPD,
        # a mean of 0.16 in Ogan Komering Ilir) were not probabilities. AUC
        # is unaffected by the weighting; calibration is.
        "scale_pos_weight": 1.0,
        "seed": RANDOM_SEED,
        "verbose": -1,
    }


def train_susceptibility(table: pd.DataFrame) -> dict:
    """Train temporal-holdout folds + a final full model; write susceptibility scores."""
    years = sorted(table["year"].unique())
    folds: list[FoldResult] = []

    for test_year in years:
        train = table[table["year"] != test_year]
        test = table[table["year"] == test_year]
        if train.empty or test.empty:
            continue
        pos = int(train["fire"].sum())
        neg = int((train["fire"] == 0).sum())
        dtrain = lgb.Dataset(train[FEATURES], label=train["fire"])
        booster = lgb.train(_params(pos, neg), dtrain, num_boost_round=300)
        proba = booster.predict(test[FEATURES])
        folds.append(FoldResult(
            train_year=int([y for y in years if y != test_year][0]) if len(years) == 2 else -1,
            test_year=int(test_year),
            roc_auc=float(roc_auc_score(test["fire"], proba)) if test["fire"].nunique() > 1 else float("nan"),
            pr_auc=float(average_precision_score(test["fire"], proba)) if test["fire"].nunique() > 1 else float("nan"),
            n_test_pos=int(test["fire"].sum()),
            prevalence=round(float(test["fire"].mean()), 4),
        ))
        log_step(f"fold test={test_year}: ROC-AUC={folds[-1].roc_auc:.3f} "
                 f"PR-AUC={folds[-1].pr_auc:.3f}", "OK")

    # final model on all data for susceptibility surface + SHAP
    pos = int(table["fire"].sum())
    neg = int((table["fire"] == 0).sum())
    dfull = lgb.Dataset(table[FEATURES], label=table["fire"])
    final = lgb.train(_params(pos, neg), dfull, num_boost_round=400)

    scores = table[["cell_id", "district", "year", "month", "fire", "peat_likely", "peat_share"]].copy()
    scores["susceptibility"] = final.predict(table[FEATURES])
    scores_path = DATA_PROCESSED / "susceptibility_scores.parquet"
    scores.to_parquet(scores_path, index=False)

    model_path = DATA_PROCESSED / "lgbm_susceptibility.txt"
    final.save_model(str(model_path))

    metrics = {
        "features": FEATURES,
        "folds": [vars(f) for f in folds],
        "n_rows": int(len(table)),
        "n_fire_positive": pos,
        "prevalence": round(pos / len(table), 4),
    }
    (OUT_TABLES / "model_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8")
    log_step(f"susceptibility model trained; prevalence={metrics['prevalence']}", "OK")

    return {"model_path": str(model_path), "scores_path": str(scores_path),
            "metrics": metrics, "booster": final, "table": table}
