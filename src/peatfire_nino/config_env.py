from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from peatfire_nino.config import project_root


@dataclass(frozen=True)
class Settings:
    gee_project_id: str
    gee_service_account: str
    gee_key_file: str
    cds_api_url: str
    cds_api_key: str
    copernicus_user: str


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise RuntimeError(
            f"Missing required setting '{key}'. "
            f"Copy credentials/credentials.env.example to credentials/credentials.env "
            f"and fill '{key}'."
        )
    return val


def load_settings() -> Settings:
    """Read credentials/credentials.env and validate required keys."""
    env_path = project_root() / "credentials" / "credentials.env"
    if not env_path.exists():
        raise FileNotFoundError(
            f"credentials.env not found at {env_path}. "
            f"Run: copy credentials\\credentials.env.example credentials\\credentials.env"
        )
    load_dotenv(env_path, override=True)

    key_file = _require("GEE_KEY_FILE")
    if not Path(key_file).exists():
        raise FileNotFoundError(
            f"GEE service-account key not found at {key_file}. "
            f"Check GEE_KEY_FILE in credentials.env."
        )

    return Settings(
        gee_project_id=_require("GEE_PROJECT_ID"),
        gee_service_account=_require("GEE_SERVICE_ACCOUNT"),
        gee_key_file=key_file,
        cds_api_url=os.getenv("CDS_API_URL", "https://cds.climate.copernicus.eu/api").strip(),
        cds_api_key=os.getenv("CDS_API_KEY", "").strip(),
        copernicus_user=os.getenv("COPERNICUS_USER", "").strip(),
    )
