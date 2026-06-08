from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REQUIRED = (
    "dataset_name", "source", "source_url", "license", "access_date",
    "spatial_resolution", "temporal_coverage", "preprocessing_steps",
    "unit", "citation_apa", "citation_bibtex", "crs",
)


def write_metadata(target: Path, fields: dict[str, Any]) -> Path:
    """Write target.metadata.json next to target, validating required keys."""
    missing = [k for k in _REQUIRED if k not in fields]
    if missing:
        raise ValueError(f"metadata for {target.name} missing keys: {missing}")

    size_mb = round(target.stat().st_size / (1024 * 1024), 3) if target.exists() else None
    payload = dict(fields)
    payload["file_size_mb"] = size_mb

    sidecar = target.with_suffix(target.suffix + ".metadata.json")
    sidecar.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return sidecar
