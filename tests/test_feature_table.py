from __future__ import annotations

from peatfire_nino.model.susceptibility import FEATURES


def test_feature_list_stable() -> None:
    expected = {"vpd", "wind_speed", "precip_mm", "treecover", "loss_frac",
                "elevation", "slope", "peat_share", "peat_thickness_cm",
                "ndwi_lag1", "lst_lag1", "sm_lag1",
                "vpd_lag1", "precip_lag1", "precip_cum2"}
    assert set(FEATURES) == expected


def test_no_label_in_features() -> None:
    assert "fire" not in FEATURES
    assert "frp_sum" not in FEATURES  # prevent target leakage


def test_no_same_month_surface_state() -> None:
    # Same-month NDWI, LST and soil moisture are observed after the burn and
    # leak the label; only their previous-month values may enter the model.
    for leaky in ("ndwi", "lst", "sm"):
        assert leaky not in FEATURES
