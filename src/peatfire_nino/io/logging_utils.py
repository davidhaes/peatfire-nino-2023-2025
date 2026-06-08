from __future__ import annotations

import logging
from datetime import datetime, timezone

from peatfire_nino.io.paths import RUN_LOG, ensure_dirs

_LEVELS = {"INFO", "WARN", "ERROR", "OK"}

_logger = logging.getLogger("peatfire")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    _logger.addHandler(_h)


def log_step(message: str, level: str = "INFO") -> None:
    """Write message to console and append to run_log.md."""
    level = level.upper()
    if level not in _LEVELS:
        level = "INFO"
    ensure_dirs()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    line = f"- `{ts}` **{level}** {message}\n"
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
    {"INFO": _logger.info, "OK": _logger.info,
     "WARN": _logger.warning, "ERROR": _logger.error}[level](message)
