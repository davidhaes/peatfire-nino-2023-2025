from __future__ import annotations

import json

import numpy as np
import pandas as pd
import shap

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import OUT_TABLES
from peatfire_nino.model.susceptibility import FEATURES


def compute_shap(model, table: pd.DataFrame) -> dict:
    """Return global + per-district mean |SHAP| and save CSV/JSON artefacts."""
    explainer = shap.TreeExplainer(model)
    # A plain random sample, so the attribution describes the landscape the
    # model is applied to rather than a fire-enriched subset of it.
    sample = table.sample(min(60000, len(table)), random_state=42) if len(table) > 60000 else table
    sv = explainer.shap_values(sample[FEATURES])
    # binary LightGBM TreeSHAP may return single array; normalise
    sv_arr = sv[1] if isinstance(sv, list) else sv

    global_imp = pd.Series(np.abs(sv_arr).mean(axis=0), index=FEATURES).sort_values(ascending=False)

    per_region = {}
    for district, idx in sample.groupby("district").groups.items():
        rows = sample.index.get_indexer(idx)
        imp = np.abs(sv_arr[rows]).mean(axis=0)
        s = pd.Series(imp, index=FEATURES).sort_values(ascending=False)
        per_region[str(district)] = {
            "ranking": list(s.index),
            "mean_abs_shap": {k: round(float(v), 5) for k, v in s.items()},
            "top_driver": s.index[0],
        }

    # rank-correlation across regions to quantify heterogeneity (H1)
    rank_df = pd.DataFrame({d: pd.Series(
        {f: r for r, f in enumerate(v["ranking"])}) for d, v in per_region.items()})
    spearman = rank_df.corr(method="spearman")

    out = {
        "global_ranking": list(global_imp.index),
        "global_mean_abs_shap": {k: round(float(v), 5) for k, v in global_imp.items()},
        "per_district": per_region,
        "between_district_rank_spearman": spearman.round(3).to_dict(),
        "heterogeneity_note": "Lower mean off-diagonal Spearman = more heterogeneous drivers (H1).",
    }
    (OUT_TABLES / "shap_attribution.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    global_imp.to_csv(OUT_TABLES / "shap_global_importance.csv", header=["mean_abs_shap"])

    off_diag = spearman.values[~np.eye(len(spearman), dtype=bool)]
    log_step(f"SHAP done; mean between-district rank corr={off_diag.mean():.3f}", "OK")
    out["_shap_values"] = sv_arr
    out["_sample"] = sample
    return out
