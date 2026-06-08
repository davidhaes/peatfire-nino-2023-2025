from __future__ import annotations

import sys

from peatfire_nino.config import STUDY_YEARS
from peatfire_nino.data.era5 import fetch_era5_predictors
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW
from peatfire_nino.io.storage_guard import enforce_cap


def main() -> int:
    log_step("stage ingest_climate started", "INFO")
    for year in STUDY_YEARS:
        df = fetch_era5_predictors(year)
        log_step(f"ERA5 {year}: {len(df)} cells", "INFO")
    size = enforce_cap(DATA_RAW)
    log_step(f"data/raw size: {size:.2f} GB", "INFO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
