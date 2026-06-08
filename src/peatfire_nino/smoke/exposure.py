from __future__ import annotations

import json

import ee
import geopandas as gpd
import numpy as np
import pandas as pd

from peatfire_nino.config import (DRY_SEASON_MONTHS, GEE_ASSETS,
                                  HIGH_ACTIVITY_QUANTILE, STUDY_YEARS)
from peatfire_nino.data.aoi import load_districts
from peatfire_nino.data.firms import fetch_firms
from peatfire_nino.io.gee_session import init_earth_engine
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import DATA_PROCESSED, OUT_TABLES


def _daily_winds_for_district(geom: ee.Geometry, year: int) -> pd.DataFrame:
    """Daily mean u10/v10 over a district for the dry season."""
    coll = (ee.ImageCollection(GEE_ASSETS["era5_land_daily"])
            .filterDate(f"{year}-06-01", f"{year}-11-30")
            .select(["u_component_of_wind_10m", "v_component_of_wind_10m"]))

    def reduce_day(im):
        stats = im.reduceRegion(ee.Reducer.mean(), geom, scale=10000, maxPixels=1e9)
        return ee.Feature(None, {
            "date": im.date().format("YYYY-MM-dd"),
            "u10": stats.get("u_component_of_wind_10m"),
            "v10": stats.get("v_component_of_wind_10m"),
        })

    feats = coll.map(reduce_day).getInfo()["features"]
    rows = [f["properties"] for f in feats]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.dropna(subset=["u10", "v10"])


def _bearing(u: float, v: float) -> float:
    """Meteorological wind direction TO (degrees from north, clockwise)."""
    # wind blows toward (u, v); bearing of transport
    ang = np.degrees(np.arctan2(u, v)) % 360.0
    return float(ang)


def export_bearing_per_district() -> dict:
    """Compute FRP-weighted export bearing per district on high-activity days."""
    init_earth_engine()
    aoi = load_districts()
    results = []
    trajectories = []

    for _, row in aoi.iterrows():
        geom = ee.Geometry(row.geometry.__geo_interface__)
        cent = row.geometry.centroid
        for year in STUDY_YEARS:
            winds = _daily_winds_for_district(geom, year)
            fires = fetch_firms(year)
            fires = fires[fires["district"] == row["district"]].copy()
            fires["acq_date"] = pd.to_datetime(fires["acq_date"], errors="coerce")
            daily_frp = fires.groupby(fires["acq_date"].dt.date)["frp"].sum()
            if daily_frp.empty:
                continue
            thresh = daily_frp.quantile(HIGH_ACTIVITY_QUANTILE)
            high_days = set(daily_frp[daily_frp >= thresh].index)

            w = winds[winds["date"].dt.date.isin(high_days)]
            if w.empty:
                continue
            # FRP-weight each high day
            weights = np.array([daily_frp.get(d.date(), 0.0) for d in w["date"]])
            u_w = np.average(w["u10"], weights=weights)
            v_w = np.average(w["v10"], weights=weights)
            bearing = _bearing(u_w, v_w)
            speed = float(np.hypot(u_w, v_w))

            results.append({
                "district": row["district"], "year": year,
                "export_bearing_deg": round(bearing, 1),
                "mean_wind_ms": round(speed, 2),
                "n_high_days": len(high_days),
                "frp_on_high_days": round(float(daily_frp[daily_frp >= thresh].sum()), 1),
            })
            # 24h straight-line forward trajectory proxy from centroid
            dist_km = speed * 3600 * 24 / 1000.0
            dlat = (dist_km / 111.0) * np.cos(np.radians(bearing))
            dlon = (dist_km / (111.0 * np.cos(np.radians(cent.y)))) * np.sin(np.radians(bearing))
            trajectories.append({
                "district": row["district"], "year": year,
                "start_lon": cent.x, "start_lat": cent.y,
                "end_lon": cent.x + dlon, "end_lat": cent.y + dlat,
                "bearing_deg": round(bearing, 1), "dist_km_24h": round(dist_km, 1),
            })

    res_df = pd.DataFrame(results)
    res_df.to_csv(OUT_TABLES / "smoke_export_bearing.csv", index=False)
    traj_df = pd.DataFrame(trajectories)
    traj_df.to_parquet(DATA_PROCESSED / "smoke_trajectories.parquet", index=False)

    # transboundary flag: bearings 270-360 (toward Malacca/NW) for Sumatra districts
    nw = res_df[(res_df["export_bearing_deg"] >= 270) | (res_df["export_bearing_deg"] <= 30)]
    out = {
        "records": results,
        "n_transboundary_oriented": int(len(nw)),
        "note": "Proxy only: straight-line ERA5 wind transport, not physical dispersion.",
    }
    (OUT_TABLES / "smoke_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    log_step(f"smoke export computed for {len(results)} district-years", "OK")
    return out
