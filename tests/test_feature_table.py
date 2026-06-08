from __future__ import annotations

from peatfire_nino.model.susceptibility import FEATURES


def test_feature_list_stable() -> None:
    expected = {"vpd", "wind_speed", "precip_mm", "treecover", "loss_frac",
                "elevation", "slope", "peat_likely"}
    assert set(FEATURES) == expected


def test_no_label_in_features() -> None:
    assert "fire" not in FEATURES
    assert "frp_sum" not in FEATURES  # prevent target leakage
