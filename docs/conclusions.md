# Conclusions

> Generated from `outputs/insights/findings.json` by `scripts/build_reports.py`. Do not edit by hand.

## Answers to the research questions

**RQ1. Drivers.** By mean absolute SHAP value the strongest predictors are VPD, Peat Thickness, Soil Moisture (prev month).
The strongest pairwise interaction is VPD with Peat Thickness (mean absolute SHAP interaction 0.049, log-odds).

**RQ2. Hotspots.** Emerging hotspot analysis classes 299 cells as intensifying, 40 as new, 0 as persistent and 48 as diminishing.

**RQ3. El Nino.** Share of peat cell-months with MODIS fire by season: 2023: 0.1210, 2024: 0.0226, 2025: 0.0079.
Monthly fire pixels correlate with ONI (OISST) at r = 0.656 over 18 months; a season-block permutation gives p = 0.167. With 3 seasons the data are consistent with an El Nino effect but cannot establish it.

**RQ4. Smoke.** 14 of 15 district-seasons have a fire-weighted wind bearing between west and north on high-activity days. This is a wind proxy, not a dispersion model.

## Model skill

Leave-one-year-out (trains on the other two seasons): 2023 ROC-AUC 0.75, PR-AUC 0.191 against prevalence 0.100; 2024 ROC-AUC 0.75, PR-AUC 0.062 against prevalence 0.023; 2025 ROC-AUC 0.61, PR-AUC 0.023 against prevalence 0.013.
Leave-one-district-out mean ROC-AUC 0.768: Banyu Asin 0.83; Kotawaringin Timur 0.70; Ogan Komering Ilir 0.86; Pelalawan 0.55; Pulang Pisau 0.90.

## Districts

Highest mean modelled susceptibility on peat: Ogan Komering Ilir (0.081, observed fire rate 0.0831).

## Carbon

Burned area 306,412 ha over 2023, 2024, 2025, of which 285,986 ha on peat. Indicative CO2 from burned peat: 66.5 to 145.9 Mt.

## Limitations

1. Fire labels are MODIS active fire pixels (FIRMS in Earth Engine, 1 km, confidence >= 30). Small and short fires below MODIS detection are missed.
2. Peat extent is PEATGRIDS thickness >= 50 cm at 1 km, a modelled map rather than a survey.
3. Surface state (NDWI, LST, soil moisture) enters from the previous month, because the same month's values are altered by the fire itself.
4. Smoke direction is a fire-weighted ERA5-Land wind proxy, not a dispersion model.
5. Carbon is an order-of-magnitude range for burned peat only; fuel and emission factors come from literature ranges.
6. Leave-one-year-out ROC-AUC ranges 0.61 to 0.75; each fold trains on the other two seasons, including later ones, so this is not a forecast test.
7. Leave-one-district-out mean ROC-AUC 0.768; the weakest district is Pelalawan at 0.55.
8. Residual Moran's I = 0.3702 (p = 0.001): spatial structure the predictors do not capture remains.
9. ENSO: Pearson r = 0.656 over 18 months from 3 seasons; season-block permutation p = 0.167. Three seasons cannot establish ENSO as the cause.
