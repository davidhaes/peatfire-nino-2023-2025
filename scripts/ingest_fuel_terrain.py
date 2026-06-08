from __future__ import annotations

import sys

from peatfire_nino.data.emissions import summarise_emissions
from peatfire_nino.data.fuel_terrain import fetch_fuel_terrain
from peatfire_nino.data.peat import fetch_peat_extent
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW
from peatfire_nino.io.storage_guard import enforce_cap


def main() -> int:
    log_step("stage ingest_fuel_terrain started", "INFO")
    ft = fetch_fuel_terrain()
    peat = fetch_peat_extent()
    emis = summarise_emissions()
    log_step(f"fuel {len(ft)} cells, peat {len(peat)} cells, emissions {len(emis)} rows", "OK")
    size = enforce_cap(DATA_RAW)
    log_step(f"data/raw size: {size:.2f} GB", "INFO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
