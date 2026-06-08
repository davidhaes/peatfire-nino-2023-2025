from __future__ import annotations

import sys

from peatfire_nino.config import STUDY_YEARS
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW
from peatfire_nino.io.storage_guard import enforce_cap


def main() -> int:
    log_step("stage ingest_firms started", "INFO")
    total = 0
    for year in STUDY_YEARS:
        gdf = fetch_firms(year)
        total += len(gdf)
    log_step(f"ingest_firms done: {total} detections across years", "OK")
    size = enforce_cap(DATA_RAW)
    log_step(f"data/raw size: {size:.2f} GB", "INFO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
