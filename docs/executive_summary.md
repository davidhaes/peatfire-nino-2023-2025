# Executive Summary

## Context

The 2023 El Nino brought Indonesia's worst fire season since 2019. This study maps where peat in five high-risk districts is most prone to burn, which conditions explain it, how different 2023 was from the two seasons after it, and in which direction smoke travelled.

## Method

Open data only: MODIS active fire and burned area, ERA5-Land, MODIS surface reflectance and temperature, SMAP, PEATGRIDS, Hansen Global Forest Change and MERIT DEM. A monthly 3 km grid for June to November 2023 to 2025 feeds a gradient boosted model validated across years and across districts.

## Key findings

1. Fire on peat was concentrated in 2023: 12.1 percent of peat cell-months had fire, against 2.3 percent in 2024 and 0.8 percent in 2025. MODIS burned area was 294,255 ha in 2023 and under 8,000 ha in each later year.
2. Dry air is the strongest driver, followed by peat thickness and the dryness of the previous month. Dry air matters most where peat is deep.
3. The model ranks fire cells above non-fire cells with ROC-AUC 0.61 to 0.75 across years and 0.768 on average across held-out districts. Pelalawan, at 0.55, is poorly explained by these predictors.
4. Fire correlates with ONI (r = 0.656), but with three seasons the association cannot be separated from other differences between years (season permutation p = 0.167).
5. On the worst days, winds carried smoke between west and north in 14 of 15 district-seasons.
6. Burned peat released an indicative 66.5 to 145.9 Mt CO2 over the three seasons.

## Priorities

1. Ogan Komering Ilir has the highest susceptibility and 59 percent of burned area, so it should come first for pre-season suppression capacity.
2. Warnings should combine dry air, deep peat and a dry previous month rather than rely on one index.
3. Pelalawan needs land-use and ignition information that climate predictors do not provide.

## Correction

An audit in September 2026 corrected the fire labels, removed same-month surface predictors that leaked the outcome, replaced an elevation proxy with PEATGRIDS peat, recomputed ONI and its significance test, and limited the carbon estimate to burned peat. The README lists each change.
