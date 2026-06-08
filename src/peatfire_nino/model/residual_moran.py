"""residual_moran.py
Moran's I on model residuals to detect leftover spatial structure.
Significant autocorrelation in residuals indicates a missing spatial covariate.
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from esda.moran import Moran
from libpysal.weights import KNN

from peatfire_nino.data.aoi import build_grid, load_districts
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_TABLES
from peatfire_nino.model.susceptibility import FEATURES


def residual_moran() -> dict:
    table = pd.read_parquet(DATA_PROCESSED / "feature_table.parquet")
    model = lgb.Booster(model_file=str(DATA_PROCESSED / "lgbm_susceptibility.txt"))

    table = table.copy()
    table["pred"] = model.predict(table[FEATURES])
    table["residual"] = table["fire"] - table["pred"]

    # aggregate residual per cell (mean across months/years) for a spatial map
    cell_res = table.groupby("cell_id", as_index=False)["residual"].mean()

    grid = build_grid(load_districts())
    cells = grid[["cell_id", "geometry"]].drop_duplicates("cell_id").to_crs(3857)
    cents = cells.copy()
    cents["geometry"] = cents.geometry.centroid
    cents = cents.to_crs(4326).merge(cell_res, on="cell_id", how="inner").reset_index(drop=True)

    w = KNN.from_dataframe(cents, k=8)
    w.transform = "r"
    mi = Moran(cents["residual"].to_numpy(), w, permutations=999)

    out = {
        "morans_I": round(float(mi.I), 4),
        "expected_I": round(float(mi.EI), 4),
        "p_value": round(float(mi.p_sim), 4),
        "z_score": round(float(mi.z_sim), 3),
        "n_cells": int(len(cents)),
        "interpretation": "Moran's I near expected (~ -1/(n-1)) with high p means residuals are "
                          "spatially random (good). Significant positive I means a spatial "
                          "covariate is still missing (e.g. true peat depth, water table).",
    }
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "residual_moran.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"residual Moran's I={mi.I:.4f} (p={mi.p_sim:.4f})", "OK")
    return out


def main() -> int:
    residual_moran()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
