"""analyze_hotspots.py
Stage: emerging hotspot analysis on the fire-pixel space-time cube.
"""
from __future__ import annotations

import sys

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.spatial.emerging_hotspot import emerging_hotspot_analysis


def main() -> int:
    log_step("stage analyze_hotspots started", "INFO")
    out = emerging_hotspot_analysis()
    log_step(f"hotspot categories: {out['category_counts']}", "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
