"""emerging_hotspot.py
Emerging Hotspot Analysis on a monthly fire-pixel space-time cube.
Getis-Ord Gi* per time bin + Mann-Kendall trend -> hotspot category.
"""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pymannkendall as mk
from libpysal.weights import KNN
from esda.getisord import G_Local

from peatfire_nino.config import DRY_SEASON_MONTHS, STUDY_YEARS
from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_TABLES


def _space_time_cube(grid: gpd.GeoDataFrame) -> pd.DataFrame:
    """Fire pixels per cell per (year, month) bin.

    Intensity is the number of 1 km MODIS fire pixels in the cell that month.
    The earlier version summed the band 21 brightness temperature under the
    name FRP; brightness temperature is not a quantity that adds up.
    """
    recs = []
    for year in STUDY_YEARS:
        fires = fetch_firms(year)
        agg = fires.groupby(["cell_id", "month"], as_index=False)["n_fire_px"].sum()
        agg = agg.rename(columns={"n_fire_px": "intensity"})
        agg["year"] = year
        recs.append(agg)
    cube = pd.concat(recs, ignore_index=True)
    cube["bin"] = cube["year"].astype(str) + "-" + cube["month"].astype(str).str.zfill(2)
    return cube


def emerging_hotspot_analysis() -> dict:
    """Run Gi* per time bin + Mann-Kendall trend; classify each cell."""
    grid = build_grid(load_districts())
    cube = _space_time_cube(grid)

    cells = grid[["cell_id", "district", "geometry"]].drop_duplicates("cell_id").copy()
    cells = cells.to_crs(3857)
    cents = cells.copy()
    cents["geometry"] = cents.geometry.centroid
    cents = cents.to_crs(4326).reset_index(drop=True)

    w = KNN.from_dataframe(cents, k=8)
    w.transform = "r"

    # Every dry-season month is a bin, including months with no fire at all,
    # so the Mann-Kendall series have the same length and spacing everywhere.
    bins = [f"{y}-{m:02d}" for y in STUDY_YEARS for m in DRY_SEASON_MONTHS]
    gi_matrix = pd.DataFrame(index=cents["cell_id"].values)

    for b in bins:
        sub = cube[cube["bin"] == b][["cell_id", "intensity"]]
        vals = cents[["cell_id"]].merge(sub, on="cell_id", how="left").fillna(0.0)
        y = vals["intensity"].to_numpy()
        if y.sum() == 0:
            gi_matrix[b] = 0.0
            continue
        gi = G_Local(y, w, star=True, seed=42)
        gi_matrix[b] = gi.Zs

    categories = []
    for cid in gi_matrix.index:
        series = gi_matrix.loc[cid, bins].to_numpy(dtype=float)
        hot_bins = int(np.sum(series > 1.96))
        if hot_bins == 0:
            cat = "no_pattern"
        else:
            try:
                trend = mk.original_test(series).trend
            except Exception:
                trend = "no trend"
            frac_hot = hot_bins / len(bins)
            if trend == "increasing" and frac_hot < 0.9:
                cat = "intensifying"
            elif frac_hot >= 0.9:
                cat = "persistent"
            elif series[-1] > 1.96 and hot_bins <= 2:
                cat = "new"
            elif trend == "decreasing":
                cat = "diminishing"
            else:
                cat = "sporadic"
        categories.append({"cell_id": int(cid), "category": cat, "hot_bins": hot_bins})

    cat_df = pd.DataFrame(categories).merge(
        cells[["cell_id", "district"]], on="cell_id", how="left")
    cat_df.to_parquet(DATA_PROCESSED / "emerging_hotspots.parquet", index=False)
    gi_matrix.reset_index(names="cell_id").to_parquet(
        DATA_PROCESSED / "gistar_spacetime.parquet", index=False)

    summary = (cat_df.groupby(["district", "category"]).size()
               .reset_index(name="n_cells"))
    summary.to_csv(OUT_TABLES / "hotspot_categories.csv", index=False)

    counts = cat_df["category"].value_counts().to_dict()
    log_step(f"emerging hotspots: {counts}", "OK")
    out = {"category_counts": {k: int(v) for k, v in counts.items()},
           "n_bins": len(bins), "bins": bins}
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "hotspot_summary.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    return out
