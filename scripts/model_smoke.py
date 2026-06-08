from __future__ import annotations

import sys

from peatfire_nino.insights.findings import build_findings
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.smoke.exposure import export_bearing_per_district


def main() -> int:
    log_step("stage model_smoke started", "INFO")
    export_bearing_per_district()
    build_findings()
    log_step("smoke + findings done", "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
