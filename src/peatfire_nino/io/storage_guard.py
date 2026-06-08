from __future__ import annotations

from pathlib import Path

from peatfire_nino.io.logging_utils import log_step


class StorageCapExceeded(RuntimeError):
    pass


def folder_size_gb(folder: Path) -> float:
    """Total size of all files under folder, in GB."""
    if not folder.exists():
        return 0.0
    total = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
    return total / (1024 ** 3)


def enforce_cap(folder: Path, warn_gb: float = 8.0, stop_gb: float = 10.0) -> float:
    """Check folder size; warn or raise. Returns current size in GB."""
    size = folder_size_gb(folder)
    if size >= stop_gb:
        raise StorageCapExceeded(
            f"data folder {size:.2f} GB exceeds {stop_gb} GB cap. "
            f"Resample to coarser grid, narrow the period, or composite further."
        )
    if size >= warn_gb:
        log_step(f"data folder {size:.2f} GB nearing {stop_gb} GB cap", "WARN")
    return size
