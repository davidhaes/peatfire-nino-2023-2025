"""carbon.py
Order-of-magnitude CO2 range from burned peat.

Peat fuel consumption is applied only to burned area on peat (PEATGRIDS
thickness at least 50 cm). Burned area off peat is reported in hectares and
not converted, because surface fuel loads differ by an order of magnitude and
are not modelled here. The earlier version applied peat fuel to every burned
hectare in the districts.

Parameter ranges (to verify before any citation):
- fuel consumption 15-30 kg/m2 of peat, from burn depths of roughly 0.15-0.3 m
  at a bulk density near 0.1 g/cm3 (Page et al. 2002; Konecny et al. 2016);
- CO2 emission factor 1,550-1,700 g/kg dry peat (Stockwell et al. 2016;
  Andreae 2019).
"""
from __future__ import annotations

import json

import pandas as pd

from peatfire_nino.data.emissions import summarise_emissions
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import OUT_TABLES

FUEL_LOW_KG_M2 = 15.0
FUEL_HIGH_KG_M2 = 30.0
EF_CO2_LOW_G_KG = 1550.0
EF_CO2_HIGH_G_KG = 1700.0


def estimate_emissions() -> dict:
    ba = summarise_emissions().copy()
    if ba.empty or "burned_peat_ha" not in ba.columns:
        log_step("burned area table empty; cannot estimate emissions", "WARN")
        return {}

    m2 = ba["burned_peat_ha"] * 10000.0
    ba["co2_low_t"] = m2 * FUEL_LOW_KG_M2 * EF_CO2_LOW_G_KG / 1e6
    ba["co2_high_t"] = m2 * FUEL_HIGH_KG_M2 * EF_CO2_HIGH_G_KG / 1e6

    agg = dict(burned_ha=("burned_area_ha", "sum"), burned_peat_ha=("burned_peat_ha", "sum"),
               burned_nonpeat_ha=("burned_nonpeat_ha", "sum"),
               co2_low_t=("co2_low_t", "sum"), co2_high_t=("co2_high_t", "sum"))
    by_year = ba.groupby("year").agg(**agg).reset_index()
    by_district = ba.groupby("district").agg(**agg).reset_index().sort_values("co2_high_t", ascending=False)

    out = {
        "parameters": {
            "fuel_consumption_kg_m2": {"low": FUEL_LOW_KG_M2, "high": FUEL_HIGH_KG_M2},
            "emission_factor_co2_g_kg": {"low": EF_CO2_LOW_G_KG, "high": EF_CO2_HIGH_G_KG},
            "applies_to": "burned area on PEATGRIDS peat (thickness >= 50 cm) only",
        },
        "years": sorted(int(y) for y in ba["year"].unique()),
        "total_burned_ha": round(float(ba["burned_area_ha"].sum()), 1),
        "total_burned_peat_ha": round(float(ba["burned_peat_ha"].sum()), 1),
        "total_burned_nonpeat_ha": round(float(ba["burned_nonpeat_ha"].sum()), 1),
        "co2_estimate_range_Mt": {
            "low": round(float(ba["co2_low_t"].sum()) / 1e6, 1),
            "high": round(float(ba["co2_high_t"].sum()) / 1e6, 1),
        },
        "by_year": by_year.round(1).to_dict(orient="records"),
        "by_district": by_district.round(1).to_dict(orient="records"),
        "note": "Order-of-magnitude range from MCD64A1 burned area on peat times literature fuel "
                "and emission-factor intervals. Not a substitute for GFED. MCD64A1 misses small and "
                "smouldering fires, so burned area and emissions are both likely underestimates.",
    }
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "carbon_emissions.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"CO2 from burned peat: {out['co2_estimate_range_Mt']['low']:.1f}-"
             f"{out['co2_estimate_range_Mt']['high']:.1f} Mt", "OK")
    return out


def main() -> int:
    estimate_emissions()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
