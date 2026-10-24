# What Open Data Can and Cannot Say About Indonesia's 2023 Peat Fires

## Lead
The 2023 El Nino dried Indonesia's peatlands and brought the worst fire season since 2019. Counting hotspots shows where it burned. Agencies with a finite budget also need to know why, where fire keeps coming back, and where the smoke goes.

## The approach
I built a reproducible pipeline from open data read through Google Earth Engine: MODIS active fire and burned area, ERA5-Land weather, MODIS and SMAP surface dryness, PEATGRIDS peat thickness, Hansen forest change and MERIT terrain. Everything is reduced to a monthly 3 km grid across five peat districts in Sumatra and Kalimantan for the dry seasons of 2023, 2024 and 2025.

A gradient boosted model is validated across seasons and across districts, and SHAP values show which conditions matter. An emerging hotspot analysis finds cells where fire is trending up, and fire-weighted winds give the direction smoke left in on the worst days.

## What the data show
In 2023, 12.1 percent of peat cell-months had MODIS fire; in 2024 it was 2.3 percent and in 2025 0.8 percent. Dry air is the strongest driver, and it matters most over deep peat that followed a dry month. The model ranks burning cells well above chance in held-out seasons and districts, with one exception: Pelalawan, where climate and peat explain little and land management probably explains more.

Fire tracks the El Nino index, but three seasons are too few to separate El Nino from everything else that differed between those years. The honest statement is that the data are consistent with an El Nino effect.

## Correcting the first version
The first version of this analysis undercounted fire about 27 times, used surface dryness measured after the fires as a predictor, and treated 18 months from three seasons as independent evidence about El Nino. Each of these made the result look stronger than it was. The corrected analysis is less dramatic and more useful.

## What it means in practice
Ogan Komering Ilir had the highest susceptibility and 59 percent of the burned area, so it comes first for suppression capacity. Warnings should combine dry air, deep peat and a dry previous month. Clusters that intensified after 2023, mostly in northern Kotawaringin Timur and Pelalawan, deserve attention in ordinary seasons too.

## Limits
MODIS misses small fires, PEATGRIDS is a model rather than a survey, the smoke direction is a wind proxy, and the carbon figure (66.5 to 145.9 Mt CO2 from burned peat) is a range from literature factors.

## References
Field et al. (2016, PNAS); Giglio et al. (2018, RSE); Munoz-Sabater et al. (2021, ESSD); Hansen et al. (2013, Science); Widyastuti et al. (2025, PEATGRIDS); Getis and Ord (1992); Lundberg and Lee (2017).
