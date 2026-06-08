"""carbon.py
Order-of-magnitude CO2 emission RANGE from peat burned area.
Reported as low-high interval; all factors NEEDS VERIFICATION before publishing.
"""
from __future__ import annotations

import json

import pandas as pd

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW, OUT_TABLES

# --- Emission parameters as a RANGE (NEEDS VERIFICATION) ---
# Tropical peat fuel consumption varies widely with burn depth.
# Low: surface-dominated burns; High: deep peat combustion.
# Sources to verify: van der Werf et al. (2017, GFED4s); IPCC 2013 Wetlands Supplement.
FUEL_LOW_KG_M2 = 15.0
FUEL_HIGH_KG_M2 = 30.0
EF_CO2_LOW_G_KG = 1550.0
EF_CO2_HIGH_G_KG = 1700.0


def estimate_emissions() -> dict:
    """Estimate CO2 emission range per district-year from MCD64A1 burned area."""
    emis_path = DATA_RAW / "gfed_emissions_summary.csv"
    if not emis_path.exists():
        log_step("burned area summary missing; cannot estimate emissions", "WARN")
        return {}

    ba = pd.read_csv(emis_path)
    if ba.empty or "burned_area_ha" not in ba.columns:
        log_step("burned area table empty", "WARN")
        return {}

    ba = ba.copy()
    ba["burned_m2"] = ba["burned_area_ha"] * 10000.0
    ba["co2_low_t"] = ba["burned_m2"] * FUEL_LOW_KG_M2 * EF_CO2_LOW_G_KG / 1e6
    ba["co2_high_t"] = ba["burned_m2"] * FUEL_HIGH_KG_M2 * EF_CO2_HIGH_G_KG / 1e6

    by_year = (ba.groupby("year")
               .agg(burned_ha=("burned_area_ha", "sum"),
                    co2_low_t=("co2_low_t", "sum"),
                    co2_high_t=("co2_high_t", "sum")).reset_index())
    by_district = (ba.groupby("district")
                   .agg(burned_ha=("burned_area_ha", "sum"),
                        co2_low_t=("co2_low_t", "sum"),
                        co2_high_t=("co2_high_t", "sum")).reset_index()
                   .sort_values("co2_high_t", ascending=False))

    total_low = float(ba["co2_low_t"].sum())
    total_high = float(ba["co2_high_t"].sum())

    out = {
        "parameters": {
            "fuel_consumption_kg_m2": {"low": FUEL_LOW_KG_M2, "high": FUEL_HIGH_KG_M2},
            "emission_factor_co2_g_kg": {"low": EF_CO2_LOW_G_KG, "high": EF_CO2_HIGH_G_KG},
            "status": "NEEDS VERIFICATION - confirm against GFED4s/IPCC before publishing",
        },
        "total_burned_ha": round(float(ba["burned_area_ha"].sum()), 1),
        "co2_estimate_range_Mt": {
            "low": round(total_low / 1e6, 1),
            "high": round(total_high / 1e6, 1),
        },
        "by_year": by_year.round(1).to_dict(orient="records"),
        "by_district": by_district.round(1).to_dict(orient="records"),
        "note": "Indicative ORDER-OF-MAGNITUDE range from MCD64A1 burned area x literature "
                "fuel/EF intervals. NOT a substitute for GFED4s. Burned area is itself a 500 m "
                "product that may over-count. Report as a range, never a single figure.",
    }
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "carbon_emissions.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"CO2 estimate range: {out['co2_estimate_range_Mt']['low']:.1f}-"
             f"{out['co2_estimate_range_Mt']['high']:.1f} Mt CO2 "
             f"(indicative, NEEDS VERIFICATION)", "OK")
    return out


def main() -> int:
    estimate_emissions()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
