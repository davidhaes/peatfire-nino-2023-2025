# Methodology

## Study area

Five peat districts were selected for fire history and for contrast between peat landscapes: Ogan Komering Ilir and Banyuasin in South Sumatra, Pulang Pisau and Kotawaringin Timur in Central Kalimantan, and Pelalawan in Riau. District boundaries come from GADM 4.1.

## Analysis grid

A 3 km grid in UTM coordinates is clipped to the districts. A cell that touches two districts is assigned to the one it overlaps most, which gives 8,240 unique cells. 3 km matches the effective resolution of the coarsest dynamic input and avoids false precision. Cells without complete predictors are dropped, leaving 7,897 cells in the model.

## Fire labels

MODIS active fire from the FIRMS collection in Earth Engine (collection 6.1, 1 km) is filtered to confidence of at least 30. For each cell and month, the 1 km pixels with fire on at least one day are counted with reduceRegions over the cell polygon. The first version vectorised the fire mask and kept one centroid per connected patch, which merged neighbouring pixels. A cell-month is labelled fire when that count is at least one. The study months are June to November of 2023, 2024 and 2025; May is read only to build lagged predictors.

## Predictors

| Group | Variables | Source |
|---|---|---|
| Weather, same month | VPD (kPa), wind speed (m/s), precipitation (mm/day) | ERA5-Land daily aggregates, monthly mean |
| Weather, previous month | VPD, precipitation, and this month's plus last month's mean daily precipitation | ERA5-Land |
| Surface state, previous month only | NDWI, land surface temperature (K), surface soil moisture (m3/m3) | MOD09A1, MOD11A2, SMAP L4 |
| Fuel and terrain, static | Tree cover 2000, share of cell with forest loss 2001 to 2022, elevation, slope | Hansen GFC v1.12, MERIT DEM |
| Peat, static | Peat share of the cell and mean thickness | PEATGRIDS, thickness at least 50 cm |

VPD uses the Tetens formulation: es(T) = 0.6108 exp(17.27 T / (T + 237.3)), and VPD = es(T air) minus es(T dewpoint).

Same-month NDWI, land surface temperature and soil moisture are excluded because a fire changes them within the month it burns. Forest loss stops at 2022 so that loss caused by the 2023 fires cannot explain those fires. MODIS surface reflectance is masked with its StateQA band, and missing values stay missing rather than being set to zero.

## Model

LightGBM gradient boosted trees with a binary objective and no class reweighting, so predicted probabilities stay on the scale of the observed rate (4.5 percent of cell-months). Validation uses two schemes.

1. Leave one year out: train on two seasons and test on the third. A fold may train on later seasons, so this measures transfer between seasons, not forecasting.
2. Leave one district out: train on four districts and test on the fifth.

ROC-AUC and PR-AUC are both reported. PR-AUC is compared with the prevalence of each test fold, not with 0.5.

## Attribution

TreeSHAP gives mean absolute SHAP values (log-odds) globally and per district, plus pairwise interaction values. Partial dependence fixes one driver at each value across a random sample of cell-months and averages the predicted probability.

## Emerging hotspots

Getis-Ord Gi* is computed per monthly bin (18 bins) on fire pixel counts with 8-nearest-neighbour weights. Cells never significant at z above 1.96 are "no pattern". For the rest, a Mann-Kendall test on the Gi* series and the timing of significant bins class the cell as new, intensifying, persistent, diminishing or sporadic.

## El Nino

The Oceanic Nino Index is computed from NOAA OISST v2.1: the Nino 3.4 sea surface temperature anomaly against a 1991 to 2020 base, as a centred three-month mean. Monthly fire pixel counts are correlated with ONI (Pearson and Spearman). The 18 months come from three seasons and are not independent, so significance is judged by permuting ONI between whole seasons. That allows six arrangements, so the smallest possible p is 1/6.

## Smoke direction

For each district and season, days at or above the 90th percentile of daily fire pixels are selected. ERA5-Land 10 m winds are weighted by each day's fire count, and the mean vector gives a bearing and a straight-line 24 hour displacement. This is a direction proxy, not a dispersion model.

## Carbon

Burned area is MODIS MCD64A1, split into peat and non-peat with PEATGRIDS. CO2 is estimated for burned peat only, as area times fuel consumption (15 to 30 kg per square metre) times emission factor (1,550 to 1,700 g CO2 per kg). The result is a range, not an inventory.

## Residual diagnostics

Moran's I on cell-mean residuals tests for spatial structure that the predictors miss.

## Software

Python 3.11 with geopandas, rasterio, LightGBM, SHAP, esda, libpysal, pymannkendall and the Earth Engine Python API. The random seed is 42. The whole pipeline runs with `python run_pipeline.py`.

## References

See references.bib.
