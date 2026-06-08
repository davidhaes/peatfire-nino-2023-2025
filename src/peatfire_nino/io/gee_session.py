from __future__ import annotations

import ee

from peatfire_nino.config_env import load_settings
from peatfire_nino.io.logging_utils import log_step

_INITIALISED = False


def init_earth_engine() -> None:
    """Initialise Earth Engine once using the service account."""
    global _INITIALISED
    if _INITIALISED:
        return
    s = load_settings()
    try:
        creds = ee.ServiceAccountCredentials(s.gee_service_account, s.gee_key_file)
        ee.Initialize(creds, project=s.gee_project_id)
        # cheap sanity call; forces auth round-trip
        _ = ee.Number(1).getInfo()
    except Exception as exc:  # noqa: BLE001 - surfaced with guidance
        raise RuntimeError(
            "GEE init failed. Check that GEE_KEY_FILE path is correct and the service "
            f"account '{s.gee_service_account}' has access to project "
            f"'{s.gee_project_id}'. Original error: {exc}"
        ) from exc
    _INITIALISED = True
    log_step(f"GEE initialised for project {s.gee_project_id}", "OK")
