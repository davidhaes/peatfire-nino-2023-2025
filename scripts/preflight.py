from __future__ import annotations

import sys

import requests

from peatfire_nino.config import GADM_IDN_URL
from peatfire_nino.config_env import load_settings
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW, ensure_dirs


def _check_env() -> list[str]:
    issues: list[str] = []
    try:
        load_settings()
        log_step("credentials.env loaded and key file present", "OK")
    except Exception as exc:  # noqa: BLE001
        issues.append(str(exc))
    return issues


def _check_gee() -> list[str]:
    issues: list[str] = []
    try:
        from peatfire_nino.io.gee_session import init_earth_engine
        init_earth_engine()
    except Exception as exc:  # noqa: BLE001
        issues.append(str(exc))
    return issues


def _check_internet() -> list[str]:
    issues: list[str] = []
    # if AOI already cached, GADM connectivity is not required
    from peatfire_nino.io.paths import DATA_RAW
    if (DATA_RAW / "aoi_districts.gpkg").exists():
        log_step("AOI cached; skipping GADM connectivity check", "OK")
        return issues
    try:
        r = requests.head(GADM_IDN_URL, timeout=60, allow_redirects=True)
        if r.status_code >= 400:
            log_step(f"GADM HTTP {r.status_code}; will retry at fetch time", "WARN")
        else:
            log_step("GADM source reachable", "OK")
    except Exception as exc:  # noqa: BLE001
        log_step(f"GADM not reachable now (timeout/slow): {exc}. "
                 f"Non-blocking; retry at fetch time.", "WARN")
    return issues


def _check_writable() -> list[str]:
    issues: list[str] = []
    try:
        ensure_dirs()
        probe = DATA_RAW / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        log_step("workspace writable", "OK")
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Workspace not writable under data/raw. {exc}")
    return issues


def _check_cds_optional() -> None:
    try:
        s = load_settings()
        if not s.cds_api_key:
            log_step("CDS_API_KEY empty; using ERA5 via GEE (CDS fallback disabled)", "WARN")
        else:
            log_step("CDS_API_KEY present (fallback available)", "OK")
    except Exception:  # noqa: BLE001
        pass  # already reported in _check_env


def main() -> int:
    log_step("preflight started", "INFO")
    issues: list[str] = []
    issues += _check_env()
    issues += _check_writable()
    issues += _check_internet()
    issues += _check_gee()
    _check_cds_optional()

    if issues:
        log_step(f"preflight FAILED with {len(issues)} issue(s)", "ERROR")
        print("\nPREFLIGHT FAILED. Resolve these before fetching data:\n")
        for i, msg in enumerate(issues, 1):
            print(f"  {i}. {msg}\n")
        return 1

    log_step("preflight passed", "OK")
    print("\nPREFLIGHT OK. Safe to run the pipeline.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
