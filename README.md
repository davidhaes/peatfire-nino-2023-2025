# Peatland Fire Susceptibility, Drivers and Smoke Direction, 2023 to 2025

A reproducible geospatial study of peatland fire in five Indonesian districts across the 2023 El Nino season and the two seasons after it. It asks which conditions explain where and when peat burns, where fire clusters are emerging, how much the 2023 season differed from the later ones, and in which direction smoke travelled on the worst days. All inputs are open data read through Google Earth Engine.

This is a screening and attribution study. It is not an operational fire forecast and not a smoke dispersion model.

## Headline results

| Result | Value |
|---|---|
| Fire-positive cell-months (MODIS, 3 km cells, June to November) | 6,432 of 142,146 (4.5%) |
| Share of peat cell-months with fire | 0.121 in 2023, 0.023 in 2024, 0.008 in 2025 |
| Strongest drivers, mean absolute SHAP | VPD, peat thickness, previous-month soil moisture |
| Leave-one-year-out ROC-AUC | 0.75 (2023), 0.75 (2024), 0.61 (2025) |
| Leave-one-district-out ROC-AUC, mean | 0.768, weakest Pelalawan at 0.55 |
| Monthly fire pixels against ONI | r = 0.656 over 18 months, season-block permutation p = 0.167 |
| Emerging hotspot classes | 299 intensifying, 40 new, 48 diminishing cells |
| Burned area, MODIS MCD64A1 | 306,412 ha, of which 285,986 ha on peat |
| Indicative CO2 from burned peat | 66.5 to 145.9 Mt |
| Smoke direction proxy | 14 of 15 district-seasons carry smoke between west and north |
| Residual Moran's I | 0.370 (p = 0.001) |

Every number above is read from `outputs/insights/findings.json`, which the pipeline writes. `docs/conclusions.md` is generated from the same file.

## Study area

Five peat districts in two regions: Ogan Komering Ilir and Banyuasin in South Sumatra, Pulang Pisau and Kotawaringin Timur in Central Kalimantan, and Pelalawan in Riau. The analysis grid has 8,240 cells of 3 km; 7,897 have complete predictors and enter the model.

![Study area and active fire](outputs/figures/01_overview.png)

## Where peat is most prone to burn

![Fire susceptibility 2023](outputs/figures/02_susceptibility.png)

Modelled monthly fire probability, averaged over the 2023 dry season, on cells that are at least half peat in PEATGRIDS. Ogan Komering Ilir has the highest mean probability (0.081, observed rate 0.083), followed by Kotawaringin Timur (0.050) and Pulang Pisau (0.044). The model is trained without class reweighting, so its probabilities sit on the scale of the observed fire rate.

![Susceptibility by district and year](outputs/figures/06_yearly_panels.png)

![2023 minus 2024](outputs/figures/05_year_delta.png)

The 2023 season stands far above 2024 and 2025 in every district. The difference map subtracts the 2024 dry-season mean from 2023.

## What drives the fire

![Global driver importance](outputs/figures/chart_shap_global.png)

Vapour pressure deficit is the strongest driver by a wide margin, followed by peat thickness, soil moisture in the previous month and rainfall in the previous month. Surface state (NDWI, land surface temperature, soil moisture) enters from the previous month only, because the same month's values are altered by the fire itself.

![Partial dependence](outputs/figures/chart_partial_dependence.png)

Partial dependence on a random sample of cell-months: probability stays near 0.03 to 0.04 while VPD is below about 0.65 kPa and roughly doubles above 0.85 kPa. It rises with peat thickness up to about 2 m and falls as the previous month becomes wetter.

![Driver interactions](outputs/figures/chart_interactions.png)

The strongest pairwise interaction is VPD with peat thickness (mean absolute SHAP interaction 0.049, log-odds): dry air matters most where peat is deep.

![Driver importance by district](outputs/figures/chart_shap_by_district.png)

VPD leads in four districts. In Pelalawan peat thickness leads, and Pelalawan is also where the model transfers worst (ROC-AUC 0.55 when the district is held out), which is consistent with ignition there depending on land management that the predictors do not describe.

## Emerging hotspots

![Priority emerging hotspots](outputs/figures/03_priority_hotspots.png)

Getis-Ord Gi* is computed per monthly bin (18 bins, June to November of each season) and a Mann-Kendall test classifies the trend of each cell. Intensifying cells cluster in northern Kotawaringin Timur and in Pelalawan, where fire continued in 2024 and 2025, while the large 2023 peat fires of Ogan Komering Ilir and Pulang Pisau did not recur.

![Temporal evolution of hot clusters](outputs/figures/chart_spacetime_hotshare.png)

## El Nino

![Fire rate and burned area by year](outputs/figures/chart_year_comparison.png)

The Oceanic Nino Index is computed from NOAA OISST v2.1 (Nino 3.4, 1991 to 2020 base). Monthly fire pixels correlate with ONI at r = 0.656 over 18 months. Those months come from only three seasons, so the fair test permutes whole seasons, and it gives p = 0.167; with three seasons it cannot fall below 1/6. The data are consistent with an El Nino effect, but three seasons cannot establish it.

## Smoke direction

![Smoke export direction](outputs/figures/04_smoke_export.png)

On high-activity days, fire-weighted ERA5-Land winds at 10 m point between west and north in 14 of 15 district-seasons. This is a straight-line wind proxy, not a dispersion model, and it does not say where haze reached the ground.

![Smoke export bearing windrose](outputs/figures/chart_windrose.png)

## Carbon

![Carbon emission estimate](outputs/figures/chart_carbon_emissions.png)

MODIS MCD64A1 records 306,412 ha burned over the three seasons, 294,255 ha of it in 2023, and 285,986 ha of the total lies on PEATGRIDS peat. Applying literature ranges for peat fuel consumption (15 to 30 kg per square metre) and the CO2 emission factor (1,550 to 1,700 g per kg) to burned peat only gives 66.5 to 145.9 Mt CO2. Ogan Komering Ilir accounts for 59 percent of burned area. This is an order-of-magnitude range, not an inventory.

## Interactive map

`outputs/interactive/peatfire_explorer.html` opens in any browser without a server. Layers: observed fire per season, modelled susceptibility per season, PEATGRIDS peat, emerging hotspots and the smoke direction proxy.

## Data

1. MODIS active fire (FIRMS in Earth Engine, collection 6.1, confidence at least 30)
2. MODIS MCD64A1 burned area
3. ERA5-Land daily aggregates: temperature, dewpoint, precipitation, 10 m wind
4. MODIS MOD09A1 (NDWI) and MOD11A2 (land surface temperature)
5. SMAP L4 surface soil moisture
6. PEATGRIDS peat thickness (Widyastuti et al. 2025, CC BY 4.0)
7. Hansen Global Forest Change v1.12, loss up to 2022
8. MERIT DEM
9. NOAA OISST v2.1 for ONI
10. GADM 4.1 district boundaries

## Method in brief

Monthly features per 3 km cell for June to November 2023 to 2025, with May used only to build lags. A cell-month is labelled fire when it holds at least one MODIS fire pixel. LightGBM is validated leave-one-year-out (each fold trains on the other two seasons, so it is not a forecast test) and leave-one-district-out. Drivers are attributed with TreeSHAP, interactions and partial dependence. Hotspots use Gi* and Mann-Kendall. Full detail is in `docs/methodology.md`.

## Correction, September 2026

An audit found errors in the first version. Every result above comes from the corrected pipeline, and the earlier figures are superseded.

1. Fire labels. The first version described its labels as VIIRS with fire radiative power. They were MODIS pixels, the "FRP" was the 11 micron brightness temperature, and converting pixels to vector centroids merged neighbours, so fire was undercounted about 27 times (1,107 positive cell-months, now 6,432).
2. Leakage. NDWI, land surface temperature and soil moisture entered from the same month as the fire, after the fire had changed them, and NDWI came out as the top driver. They now enter from the previous month.
3. Peat. An elevation proxy stood in for peat. PEATGRIDS thickness now defines peat.
4. El Nino. ONI values were typed in by hand and never verified, and the correlation was tested as if 18 months were independent (reported p = 0.0018). ONI is now computed from OISST and tested by permuting seasons (p = 0.167).
5. Carbon. Peat fuel consumption was applied to all burned area. It now applies to burned peat only.
6. Grid. Cells on district borders were duplicated (8,314 cells, now 8,240).
7. Model. Class reweighting inflated the probabilities, and the partial dependence curves were not true partial dependence. Both are fixed.

## Limitations

1. MODIS misses small and short fires, and cloud and haze hide some burning.
2. PEATGRIDS is a modelled 1 km map, not a survey.
3. Three seasons cannot separate El Nino from other year-to-year differences.
4. Residual Moran's I of 0.37 shows spatial structure the predictors miss, most likely drainage and water table.
5. Smoke direction is a wind proxy, and carbon is a literature-factor range.

## Reproduce

```bash
python run_pipeline.py
```

Earth Engine access is configured in `credentials/credentials.env` (copy `credentials/credentials.env.example`). That file is git-ignored.

## License

MIT. See LICENSE.
