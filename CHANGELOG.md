# Changelog

## [0.2.0] 2026-09-27
Audit corrections. All results changed; see the Correction section of the README.
- Fire labels: MODIS pixels counted per cell with reduceRegions; no longer described as VIIRS or FRP; centroid undercount removed.
- Same-month NDWI, LST and soil moisture replaced by previous-month values to remove leakage.
- PEATGRIDS peat share and thickness replace the elevation peat proxy.
- ONI computed from OISST; season-block permutation test replaces the naive p-value.
- Carbon applied to burned peat only; 2025 included.
- Grid deduplicated at district borders (8,240 cells); May added for lags; Hansen loss capped at 2022.
- No class reweighting; true partial dependence; findings and conclusions generated from data.
- Interactive map redrawn as one layer per season, susceptibility as raster overlays.
- Chart labels carry units; precipitation is mm per day.

## [0.1.0]
- Initial reproducible pipeline: AOI, FIRMS, ERA5, fuel/terrain, peat proxy.
- LightGBM susceptibility with cross-year hold-out + SHAP attribution.
- Emerging hotspot analysis (Gi* + Mann-Kendall).
- Wind-driven smoke export proxy.
- Static maps, charts, combined interactive HTML.
- findings.json + narrative interpreter + English reports.
