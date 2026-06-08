# Executive Summary

## Context

Indonesia experienced its most severe fire season since 2019 during the 2023 El Nino. Peatland fires threaten lives, release vast carbon stocks, and produce haze that crosses national borders. This study maps where peat is most prone to burn, explains why, and traces where the smoke travels.

## Method

Using only open data from NASA FIRMS, ERA5 Land, MODIS, SMAP, Hansen Global Forest Change, and MERIT DEM, we built a monthly grid of fire predictors across five high risk districts and trained a gradient boosted susceptibility model with spatial and temporal validation.

## Key Findings

1. The strongest fire driver is vegetation and surface dryness, captured by NDWI, VPD, and soil moisture.
2. Compound dryness, the joint occurrence of dry air and dry soil, is the single most dangerous condition, with an interaction strength of 0.087.
3. The El Nino signal is clear and significant, with fire counts correlated to the Oceanic Nino Index at r = 0.684.
4. Ogan Komering Ilir is the highest risk district and should be prioritised for suppression resources.
5. The model transfers across unseen districts (mean spatial AUC 0.708), except Pelalawan, where fires appear human driven rather than climate driven.

## High Priority Recommendations

1. Pre position suppression resources in Ogan Komering Ilir before the peak dry season.
2. Trigger early warnings on compound dryness, not single indicators.
3. Issue transboundary haze pre alerts when high fire activity coincides with northwesterly winds.

## Reproducibility

The entire analysis is reproducible from open data through a single pipeline command. See the repository README for instructions.
