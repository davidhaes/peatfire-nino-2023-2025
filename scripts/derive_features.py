from __future__ import annotations

import sys

from peatfire_nino.features.feature_table import build_feature_table
from peatfire_nino.io.logging_utils import log_step


def main() -> int:
    log_step("stage derive_features started", "INFO")
    table = build_feature_table()
    log_step(f"feature table ready: {len(table)} rows", "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
