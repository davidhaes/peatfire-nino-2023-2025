"""cache.py
Cache-existence helper with consistent logging.
"""
from __future__ import annotations

from pathlib import Path

from peatfire_nino.io.logging_utils import log_step


def file_exists(path: Path, hint: str) -> bool:
    if path.exists():
        log_step(f"Using cached file {path.name}", "INFO")
        return True
    log_step(f"Downloading fresh: {hint}", "INFO")
    return False