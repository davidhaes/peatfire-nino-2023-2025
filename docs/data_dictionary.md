# Data Dictionary

## feature_table.parquet

One row per cell, month and year; 142,146 rows for June to November 2023 to 2025.

1. cell_id, integer, grid cell identifier
2. district, text, district name
3. year, integer, 2023 to 2025
4. month, integer, 6 to 11
5. vpd, float, vapour pressure deficit, kPa
6. wind_speed, float, 10 m wind speed, m/s
7. precip_mm, float, mean daily precipitation, mm/day
8. t2m_c, float, 2 m air temperature, degrees C
9. ndwi, float, same-month NDWI; kept for reference, not a model feature
10. lst_k, float, same-month land surface temperature, K; not a model feature
11. soil_moisture, float, same-month soil moisture, m3/m3; not a model feature
12. ndwi_lag1, lst_lag1, sm_lag1, float, previous-month NDWI, LST and soil moisture
13. vpd_lag1, precip_lag1, float, previous-month VPD and precipitation
14. precip_cum2, float, this month's plus last month's mean daily precipitation, mm/day
15. treecover, float, Hansen tree cover in 2000, percent
16. loss_frac, float, share of the cell with Hansen loss 2001 to 2022
17. elevation, float, m
18. slope, float, degrees
19. peat_share, float, share of the cell with PEATGRIDS peat at least 50 cm thick
20. peat_thickness_cm, float, mean PEATGRIDS thickness, cm
21. peat_likely, integer, 1 when peat_share is at least 0.5
22. n_fire_px, integer, 1 km MODIS pixels in the cell with fire on at least one day of the month
23. n_fire_days_px, integer, pixel-days, the sum over days of fire pixels in the cell
24. fire, integer, 1 when n_fire_px is at least 1

## findings.json

Top-level keys: study, model, spatial_cross_validation, drivers, driver_interactions, enso_linkage, susceptibility_by_year, susceptibility_by_district, emerging_hotspots, smoke_exposure, carbon_emissions, residual_spatial_autocorrelation, honesty_notes.
