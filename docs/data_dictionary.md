# Data Dictionary

## feature_table.parquet

Cell month records used for modelling.

1. cell_id, integer, unique grid cell identifier
2. district, text, district name
3. month, integer, month number 6 to 11
4. year, integer, 2023 to 2025
5. vpd, float, vapour pressure deficit in kilopascal
6. wind_speed, float, 10 metre wind speed in metres per second
7. precip_mm, float, monthly precipitation in millimetre
8. ndwi, float, Normalized Difference Water Index, minus 1 to plus 1
9. lst_k, float, land surface temperature in kelvin
10. soil_moisture, float, surface soil moisture, volumetric fraction
11. treecover, float, tree cover percent
12. loss_frac, float, forest loss fraction
13. elevation, float, elevation in metre
14. slope, float, slope in degree
15. peat_likely, integer, peat proxy flag 0 or 1
16. vpd_lag1, float, previous month VPD
17. precip_lag1, float, previous month precipitation
18. sm_lag1, float, previous month soil moisture
19. precip_cum2, float, two month cumulative precipitation
20. fire, integer, fire label 0 or 1
21. frp_sum, float, summed fire radiative power proxy
22. n_det, integer, detection count

## findings.json

Top level keys: model, spatial_cross_validation, drivers, driver_interactions, enso_linkage, susceptibility_by_year, susceptibility_by_district, emerging_hotspots, smoke_exposure, carbon_emissions, residual_spatial_autocorrelation, honesty_notes.
