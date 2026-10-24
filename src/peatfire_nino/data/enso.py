"""enso.py
Link monthly fire activity to ENSO.

The Oceanic Nino Index is computed here rather than typed in. The earlier
version hard-coded 18 monthly values marked "NEEDS VERIFICATION"; they were
shifted by one month against the CPC convention (June carried the April to
June value) and the 2025 values did not reflect the La Nina conditions that
developed late that year.

Index definition used here: monthly mean sea surface temperature over the
Nino 3.4 box (5N-5S, 170W-120W) from NOAA OISST v2.1, as an anomaly against
the 1991-2020 monthly climatology, smoothed with a centred three-month
running mean. The official CPC ONI uses ERSST v5; the two agree closely but
can differ by about 0.1 C in a given month, so values are labelled
"ONI (OISST)" everywhere they appear.

Statistics: with three seasons of six months each, the 18 monthly pairs are
neither independent nor enough to separate El Nino from anything else that
differed between 2023 and the two later years. The correlation is reported
as a description, with a p-value from a permutation that only swaps whole
seasons, which is the honest test for this design and cannot reach
significance with three seasons.
"""
from __future__ import annotations

import itertools
import json

import ee
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from peatfire_nino.config import DRY_SEASON_MONTHS, GEE_ASSETS, STUDY_YEARS
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.io.cache import file_exists
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_RAW, OUT_TABLES

NINO34 = [-170.0, -5.0, -120.0, 5.0]
CLIM_START, CLIM_END = 1991, 2020


def fetch_oni() -> pd.DataFrame:
    """Monthly Nino 3.4 anomaly and three-month running mean, 1991 onward."""
    out = DATA_RAW / "oni_oisst.parquet"
    if file_exists(out, "ONI from OISST"):
        return pd.read_parquet(out)

    init_earth_engine()
    box = ee.Geometry.Rectangle(NINO34, None, False)
    sst = ee.ImageCollection(GEE_ASSETS["oisst"]).select("sst")
    last_year = max(STUDY_YEARS)
    months = ee.List([
        ee.Date.fromYMD(y, m, 1) for y in range(CLIM_START, last_year + 1) for m in range(1, 13)
    ])

    def monthly_mean(d):
        d = ee.Date(d)
        img = sst.filterDate(d, d.advance(1, "month")).mean()
        val = img.reduceRegion(ee.Reducer.mean(), box, 25000, maxPixels=1e9).get("sst")
        return ee.Feature(None, {"date": d.format("YYYY-MM"), "sst": val})

    feats = ee.FeatureCollection(months.map(monthly_mean)).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in feats]).dropna()
    df["date"] = pd.to_datetime(df["date"])
    # OISST sst band is stored in hundredths of a degree
    df["sst_c"] = df["sst"].astype(float) * 0.01
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    clim = df[(df["year"] >= CLIM_START) & (df["year"] <= CLIM_END)].groupby("month")["sst_c"].mean()
    df["anom"] = df["sst_c"] - df["month"].map(clim)
    df = df.sort_values("date").reset_index(drop=True)
    df["oni"] = df["anom"].rolling(3, center=True).mean()
    df = df[["date", "year", "month", "sst_c", "anom", "oni"]]
    df.to_parquet(out, index=False)
    log_step(f"ONI (OISST) computed for {len(df)} months", "OK")
    return df


def link_enso() -> dict:
    oni = fetch_oni()
    oni_lookup = {(int(r.year), int(r.month)): float(r.oni) for r in oni.itertuples() if pd.notna(r.oni)}

    rows = []
    for year in STUDY_YEARS:
        fires = fetch_firms(year)
        by_month = fires.groupby("month")["n_fire_px"].sum()
        for m in DRY_SEASON_MONTHS:
            rows.append({
                "year": year, "month": m,
                "oni": oni_lookup.get((year, m)),
                "fire_pixels": float(by_month.get(m, 0.0)),
            })
    df = pd.DataFrame(rows).dropna(subset=["oni"])

    r_p, _ = pearsonr(df["oni"], df["fire_pixels"])
    r_s, _ = spearmanr(df["oni"], df["fire_pixels"])

    # Season-block permutation: reassign whole seasons of fire counts to the
    # seasons of ONI values. With three seasons there are six arrangements.
    seasons = sorted(df["year"].unique())
    fire_by_season = {y: df[df["year"] == y]["fire_pixels"].to_numpy() for y in seasons}
    null = []
    for perm in itertools.permutations(seasons):
        shuffled = np.concatenate([fire_by_season[y] for y in perm])
        null.append(pearsonr(df["oni"], shuffled)[0])
    null = np.array(null)
    perm_p = float((np.abs(null) >= abs(r_p) - 1e-12).mean())

    yearly = df.groupby("year").agg(
        mean_oni=("oni", "mean"), total_fire_pixels=("fire_pixels", "sum")).reset_index()

    out = {
        "index": "ONI computed from NOAA OISST v2.1, Nino 3.4, 1991-2020 base, centred 3-month mean",
        "monthly": df.to_dict(orient="records"),
        "yearly": yearly.to_dict(orient="records"),
        "pearson_r": round(float(r_p), 3),
        "spearman_r": round(float(r_s), 3),
        "n_months": int(len(df)),
        "n_seasons": int(len(seasons)),
        "season_permutation_p": round(perm_p, 3),
        "season_permutations": int(len(null)),
        "note": (
            "Descriptive. Eighteen months from three seasons cannot establish that ENSO drives "
            "the difference; the season-block permutation p cannot fall below 1/6 by construction. "
            "The comparison that carries information is between seasons."
        ),
    }
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    (OUT_TABLES / "enso_linkage.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"ENSO linkage: Pearson r={r_p:.3f}, season-permutation p={perm_p:.3f}", "OK")
    return out


def main() -> int:
    link_enso()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
