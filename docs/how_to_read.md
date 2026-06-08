# How to Read the Metrics

## Fire susceptibility
Unit: probability from 0 to 1. Higher means more likely to burn.
Bands: below 0.2 low, 0.2 to 0.5 moderate, above 0.5 high.
Example: a cell at 0.74 sits in the top risk band and warrants monitoring.

## NDWI, Normalized Difference Water Index
Unit: index from minus 1 to plus 1. Lower values mean drier vegetation.
Example: a sustained drop in NDWI signals fire prone conditions.

## VPD, Vapour Pressure Deficit
Unit: kilopascal. Higher means thirstier, drier air.
Threshold: fire probability rises sharply above roughly 0.65 kPa in this study.

## Soil moisture
Unit: volumetric fraction. Lower means drier peat and higher fire risk.

## ROC-AUC
Unit: 0.5 to 1. Measures how well the model ranks fire cells above non fire cells.
Interpretation: 0.5 is random, 0.7 is useful, above 0.8 is strong. Our temporal AUC ranges 0.62 to 0.74 and spatial mean is 0.708.

## Oceanic Nino Index, ONI
Unit: temperature anomaly in degrees Celsius. Positive values indicate El Nino.
Example: ONI of 1.8 in late 2023 marks a strong El Nino, coinciding with peak fire.

## Moran's I on residuals
Unit: minus 1 to plus 1. Near zero means model errors are spatially random, which is good.
Our value of 0.5453 indicates leftover spatial structure, pointing to a missing peat depth or water table layer.
