"""train_susceptibility.py
Stage: train LightGBM susceptibility + SHAP attribution.
"""
from __future__ import annotations

import sys

from peatfire_nino.features.feature_table import build_feature_table
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.model.attribution import compute_shap
from peatfire_nino.model.susceptibility import train_susceptibility


def main() -> int:
    log_step("stage train_susceptibility started", "INFO")
    table = build_feature_table()
    result = train_susceptibility(table)
    compute_shap(result["booster"], result["table"])
    log_step("susceptibility + attribution done", "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
