from __future__ import annotations

import numpy as np

from peatfire_nino.features.vpd import vpd_kpa


def test_vpd_positive_when_dry() -> None:
    v = vpd_kpa(np.array([30.0]), np.array([20.0]))
    assert 1.5 < float(v[0]) < 2.5


def test_vpd_zero_when_saturated() -> None:
    v = vpd_kpa(np.array([25.0]), np.array([25.0]))
    assert float(v[0]) == 0.0


def test_vpd_clips_negative() -> None:
    v = vpd_kpa(np.array([20.0]), np.array([25.0]))
    assert float(v[0]) == 0.0
