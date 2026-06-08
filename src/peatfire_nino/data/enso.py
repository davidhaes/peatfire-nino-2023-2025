"""enso.py
Link monthly fire activity to the Oceanic Nino Index (ONI).
Quantifies the El Nino -> dryness -> fire chain.
ONI values are hardcoded from NOAA CPC (public, monthly 3-month running mean).
"""
from __future__ import annotations

import json

import pandas as pd
from scipy.stats import pearsonr, spearmanr

from peatfire_nino.config import DRY_SEASON_MONTHS, STUDY_YEARS
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import OUT_TABLES

# NOAA CPC ONI, 3-month running mean centered on month. Public data.
# Source: https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php
# NEEDS VERIFICATION before publish: confirm exact ONI values from CPC.
ONI = {
    (2023, 6): 0.5, (2023, 7): 0.8, (2023, 8): 1.1, (2023, 9): 1.3,
    (2023, 10): 1.6, (2023, 11): 1.8,
    (2024, 6): 0.2, (2024, 7): -0.1, (2024, 8): -0.3, (2024, 9): -0.4,
    (2024, 10): -0.6, (2024, 11): -0.7,
    (2025, 6): -0.1, (2025, 7): 0.0, (2025, 8): 0.1, (2025, 9): 0.1,
    (2025, 10): 0.2, (2025, 11): 0.2,
}


def link_enso() -> dict:
    grid = build_grid(load_districts())
    rows = []
    for year in STUDY_YEARS:
        fires = fetch_firms(year)
        import geopandas as gpd
        joined = gpd.sjoin(fires, grid[["cell_id", "geometry"]],
                           predicate="within", how="inner")
        by_month = joined.groupby("month").size()
        for m in DRY_SEASON_MONTHS:
            rows.append({
                "year": year, "month": m,
                "oni": ONI.get((year, m)),
                "fire_count": int(by_month.get(m, 0)),
            })
    df = pd.DataFrame(rows).dropna(subset=["oni"])

    r_p, p_p = pearsonr(df["oni"], df["fire_count"])
    r_s, p_s = spearmanr(df["oni"], df["fire_count"])

    # yearly totals for the headline contrast
    yearly = df.groupby("year").agg(
        mean_oni=("oni", "mean"), total_fire=("fire_count", "sum")).reset_index()

    out = {
        "monthly": df.to_dict(orient="records"),
        "yearly": yearly.to_dict(orient="records"),
        "pearson_r": round(float(r_p), 3),
        "pearson_p": round(float(p_p), 4),
        "spearman_r": round(float(r_s), 3),
        "spearman_p": round(float(p_s), 4),
        "note": "ONI from NOAA CPC (NEEDS VERIFICATION). Positive correlation links "
                "El Nino strength to dry-season fire activity.",
    }
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "enso_linkage.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"ENSO linkage: Pearson r={r_p:.3f} (p={p_p:.4f}), "
             f"Spearman r={r_s:.3f}", "OK")
    return out


def main() -> int:
    link_enso()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
