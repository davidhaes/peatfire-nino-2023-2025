from __future__ import annotations

from pathlib import Path

from peatfire_nino.config import project_root

ROOT = project_root()

DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
OUT_FIGURES = ROOT / "outputs" / "figures"
OUT_INTERACTIVE = ROOT / "outputs" / "interactive"
OUT_INSIGHTS = ROOT / "outputs" / "insights"
OUT_TABLES = ROOT / "outputs" / "tables"
RUN_LOG = ROOT / "outputs" / "run_log.md"
DOCS = ROOT / "docs"

_ALL_DIRS = (
    DATA_RAW, DATA_INTERIM, DATA_PROCESSED,
    OUT_FIGURES, OUT_INTERACTIVE, OUT_INSIGHTS, OUT_TABLES, DOCS,
)


def ensure_dirs() -> None:
    """Create every output/data directory if missing."""
    for d in _ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)
