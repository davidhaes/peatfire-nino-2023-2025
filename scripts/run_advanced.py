"""run_advanced.py
Stage: run all advanced analyses so findings.json is complete.
Interaction, spatial CV, ENSO linkage, carbon, residual Moran, then rebuild findings.
"""
from __future__ import annotations

import sys

from peatfire_nino.io.logging_utils import log_step


def main() -> int:
    log_step("stage run_advanced started", "INFO")
    from peatfire_nino.model.interaction import compute_interactions
    from peatfire_nino.model.spatial_cv import spatial_cross_validate
    from peatfire_nino.model.residual_moran import residual_moran
    from peatfire_nino.data.enso import link_enso
    from peatfire_nino.data.carbon import estimate_emissions
    from peatfire_nino.insights.findings import build_findings

    for name, fn in [
        ("interaction", compute_interactions),
        ("spatial CV", spatial_cross_validate),
        ("ENSO linkage", link_enso),
        ("carbon", estimate_emissions),
        ("residual Moran", residual_moran),
    ]:
        try:
            fn()
            log_step(f"advanced: {name} done", "OK")
        except Exception as exc:
            log_step(f"advanced: {name} failed: {exc}", "WARN")

    build_findings()
    log_step("run_advanced done; findings.json rebuilt", "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
