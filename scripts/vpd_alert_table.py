"""Observed fire rate on peat by dryness band and peat depth.

The partial dependence plot shows the model's response to vapour pressure
deficit. This table checks the same threshold against the data alone: the
share of peat cell-months with MODIS fire in each VPD band, split by peat
thickness (deep means 1.5 m or more), for all three seasons and for 2024 and 2025 without the El Niño
year. If the step survives without 2023, the alert is not just a proxy for
El Niño.

Writes outputs/tables/vpd_alert_table.csv.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BANDS = [-np.inf, 0.65, 0.85, np.inf]
BAND_LABELS = ["below 0.65 kPa", "0.65 to 0.85 kPa", "above 0.85 kPa"]


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/feature_table.parquet")
    peat = d[d["peat_likely"] == 1].copy()
    peat["vpd_band"] = pd.cut(peat["vpd"], BANDS, labels=BAND_LABELS)
    peat["depth"] = np.where(peat["peat_thickness_cm"] >= 150, "deep", "shallow")
    rows = []
    for scope, sub in (("2023 to 2025", peat), ("2024 and 2025", peat[peat["year"] != 2023])):
        for depth in ("all", "shallow", "deep"):
            s = sub if depth == "all" else sub[sub["depth"] == depth]
            g = s.groupby("vpd_band", observed=False)["fire"].agg(["mean", "size"])
            for band, r in g.iterrows():
                rows.append({"seasons": scope, "peat_depth": depth, "vpd_band": band,
                             "fire_rate": round(float(r["mean"]), 4), "n_cell_months": int(r["size"])})
    out = pd.DataFrame(rows)
    path = ROOT / "outputs/tables/vpd_alert_table.csv"
    out.to_csv(path, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
