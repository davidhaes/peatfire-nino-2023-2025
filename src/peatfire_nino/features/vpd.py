from __future__ import annotations

import numpy as np


def _tetens_kpa(temp_c: np.ndarray) -> np.ndarray:
    """Saturation vapor pressure (kPa) via Tetens over water."""
    return 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))


def vpd_kpa(t2m_c: np.ndarray, td2m_c: np.ndarray) -> np.ndarray:
    """Vapor pressure deficit in kPa. Negative artefacts clipped to 0."""
    es_t = _tetens_kpa(np.asarray(t2m_c, dtype=float))
    es_td = _tetens_kpa(np.asarray(td2m_c, dtype=float))
    return np.clip(es_t - es_td, 0.0, None)
