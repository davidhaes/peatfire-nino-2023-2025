from __future__ import annotations

import argparse
import importlib
import sys

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW
from peatfire_nino.io.storage_guard import folder_size_gb

# (module path, friendly name)
STAGES = [
    ("scripts.prepare", "prepare AOI + grid"),
    ("scripts.ingest_firms", "fetch FIRMS"),
    ("scripts.ingest_climate", "fetch ERA5"),
    ("scripts.ingest_fuel_terrain", "fetch fuel/terrain/peat/emissions"),
    ("scripts.derive_features", "build feature table"),
    ("scripts.train_susceptibility", "train + attribution"),
    ("scripts.analyze_hotspots", "emerging hotspots"),
    ("scripts.model_smoke", "smoke + findings"),
    ("scripts.run_advanced", "advanced analysis (interaction, spatial CV, ENSO, carbon, Moran)"),
    ("scripts.make_figures", "figures + interactive"),
    ("scripts.build_reports", "reports"),
]


def _run_stage(module_path: str) -> int:
    mod = importlib.import_module(module_path)
    return int(mod.main())


def main() -> int:
    parser = argparse.ArgumentParser(description="peatfire-nino pipeline")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--skip-preflight", action="store_true",
                        help="not recommended; only for reruns after a verified preflight")
    args = parser.parse_args()

    if not args.skip_preflight:
        from scripts.preflight import main as preflight_main
        if preflight_main() != 0:
            log_step("pipeline aborted: preflight failed", "ERROR")
            return 1

    failures = 0
    for module_path, name in STAGES:
        log_step(f"=== stage: {name} ===", "INFO")
        try:
            rc = _run_stage(module_path)
            if rc != 0:
                raise RuntimeError(f"stage '{name}' returned {rc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            log_step(f"stage '{name}' failed: {exc}", "ERROR")
            if not args.continue_on_error:
                log_step("stopping (use --continue-on-error to proceed)", "ERROR")
                return 1

    size = folder_size_gb(DATA_RAW)
    log_step(f"pipeline complete. data/raw size: {size:.2f} GB. failures: {failures}", "OK")
    print(f"\nPIPELINE DONE. data/raw = {size:.2f} GB, failed stages = {failures}\n")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
