# Methodology

## Study Area

Five peat dominated districts were selected across two macro regions: Ogan Komering Ilir and Banyuasin in South Sumatra, Pulang Pisau and Kotawaringin Timur in Central Kalimantan, and Pelalawan in Riau. Selection was based on documented fire history, with Ogan Komering Ilir an epicentre of the 2015 crisis, and on the contrast between deep coastal peat domes, ex Mega Rice Project drainage landscapes, and industrial plantation adjacent peat.

## Data Sources

1. NASA FIRMS VIIRS S-NPP active fire and fire radiative power, accessed through the Earth Engine FIRMS collection (Schroeder et al., 2014).
2. ERA5 Land daily aggregated reanalysis for 2 metre temperature, dewpoint, total precipitation, and 10 metre winds (Munoz-Sabater et al., 2021).
3. MODIS MOD09A1 surface reflectance for the Normalized Difference Water Index, and MOD11A2 for land surface temperature.
4. NASA SMAP Level 4 surface soil moisture (Entekhabi et al., 2010).
5. Hansen Global Forest Change for tree cover baseline and forest loss (Hansen et al., 2013).
6. MERIT DEM for elevation and derived slope (Yamazaki et al., 2017).
7. MODIS MCD64A1 burned area for emission context (Giglio et al., 2018).
8. GADM 4.1 administrative boundaries.

## Pre-processing Pipeline

District boundaries were retrieved from GADM and used to construct a 3 kilometre analysis grid in projected UTM coordinates, yielding 8,314 cells. The 3 kilometre resolution was chosen to match the effective resolution of ERA5 Land and to avoid false precision, since predicting at a resolution finer than the coarsest input would be misleading. All raster predictors were reduced to grid cell centroids using Earth Engine reduceRegions in batches of 2,000 cells to respect platform query limits. Fire detections were aggregated to monthly cell level binary labels.

## Feature Engineering

The feature table combines static predictors (elevation, slope, tree cover, forest loss, peat proxy), monthly climate (vapour pressure deficit, wind speed, precipitation), monthly dynamic dryness (NDWI, land surface temperature, soil moisture), and temporal lag features (previous month VPD, precipitation, and soil moisture, plus two month cumulative precipitation). The final table contains 143,478 cell month records with 1,107 fire positive cases, a prevalence of 0.77 percent.

Vapour pressure deficit was computed from temperature and dewpoint using the Tetens formulation:

es(T) = 0.6108 exp( 17.27 T / (T + 237.3) )

VPD = es(T_air) minus es(T_dewpoint), expressed in kilopascal.

## Analytical Methods

Fire susceptibility was modelled with LightGBM gradient boosted trees (Ke et al., 2017), using scale_pos_weight to address class imbalance. Validation used two complementary strategies. Temporal hold out trained on two years and tested on the third, repeated for each year. Leave one district out spatial cross validation trained on four districts and tested on the fifth, repeated for each district, to test whether the model captures transferable mechanism rather than location memory.

Driver attribution used TreeSHAP (Lundberg and Lee, 2017), including global mean absolute SHAP, per district attribution, pairwise interaction values, and partial dependence. Emerging hotspots were detected with the Getis-Ord Gi star statistic (Getis and Ord, 1992) computed per monthly time bin on a K nearest neighbour spatial weights matrix, with a Mann-Kendall trend test classifying each cell as new, intensifying, persistent, diminishing, sporadic, or no pattern. Fire counts were correlated with the Oceanic Nino Index using Pearson and Spearman coefficients. Residual spatial autocorrelation was tested with Moran's I to diagnose missing covariates.

## Validation Strategy

Because fire positive cells are rare, model skill is reported with both ROC-AUC and PR-AUC, the latter compared against prevalence rather than 0.5. Temporal AUC ranged from 0.62 to 0.74. Spatial cross validation produced a mean AUC of 0.708, indicating that the learned mechanism transfers across unseen districts, with the notable exception of Pelalawan.

## Software and Reproducibility

The analysis uses Python 3.11 with geopandas, rasterio, LightGBM, SHAP, esda and libpysal, pymannkendall, and the Earth Engine Python API. A fixed random seed of 42 ensures reproducibility. The complete pipeline runs from a single command.

## References

See references.bib for full citations.
