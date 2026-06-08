from __future__ import annotations

import sys

from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW
from peatfire_nino.io.storage_guard import enforce_cap


def main() -> int:
    log_step("stage prepare started", "INFO")
    districts = load_districts()
    grid = build_grid(districts)
    log_step(f"prepare done: {len(districts)} districts, {len(grid)} grid cells", "OK")
    size = enforce_cap(DATA_RAW)
    log_step(f"data/raw size: {size:.2f} GB", "INFO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
