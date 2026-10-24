# How to Read the Metrics

## Fire susceptibility
Modelled probability that a 3 km cell has at least one MODIS fire pixel in a given month. The model is not reweighted, so values sit near the observed rate: 4.5 percent of cell-months overall and 12.1 percent of peat cell-months in 2023. A cell at 0.25 is several times more likely to burn that month than the average cell.

## VPD, vapour pressure deficit
kPa. Higher means drier air. In this study modelled probability rises clearly above about 0.65 kPa.

## Peat thickness
cm, from PEATGRIDS. A cell counts as peat when at least half of it has peat at least 50 cm thick.

## Precipitation
mm per day, the monthly mean of ERA5-Land daily totals.

## Soil moisture
m3/m3, SMAP L4 surface layer, taken from the previous month.

## SHAP values
Log-odds contribution of a predictor to one prediction. Mean absolute SHAP ranks predictors by how much they move predictions on average.

## ROC-AUC
Probability that a random fire cell-month is ranked above a random non-fire one. 0.5 is chance. Here 0.61 to 0.75 across years and 0.768 on average across districts.

## PR-AUC
Average precision. Compare it with the prevalence of the test fold, not with 0.5: 0.191 against a prevalence of 0.100 in 2023 means the model roughly doubles precision over random ranking.

## ONI
Oceanic Nino Index in degrees C, computed from OISST. Above 0.5 is El Nino. It peaked near 1.8 in late 2023.

## Moran's I on residuals
Near zero means model errors are spatially random. 0.37 here means neighbouring cells share errors, so a spatial predictor is missing.
