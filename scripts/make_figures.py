from __future__ import annotations

import sys

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.viz.charts import render_charts
from peatfire_nino.viz.interactive import build_interactive_map
from peatfire_nino.viz.maps_static import render_static_maps


def main() -> int:
    log_step("stage make_figures started", "INFO")
    render_static_maps()
    render_charts()
    build_interactive_map()
    log_step("make_figures done", "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
