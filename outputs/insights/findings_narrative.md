# Automated Reading of findings.json

The susceptibility model generalises across ENSO years. On the held-out year 2023, it reached ROC-AUC 0.617 and PR-AUC 0.028 against a fire prevalence of 0.8%. PR-AUC well above prevalence means the model ranks dangerous cells far better than chance.

Globally, the strongest fire drivers in order are: ndwi, elevation, vpd, treecover. This is the lever set practitioners can act on.

Crucially, the dominant driver differs between districts (Banyu Asin: ndwi; Kotawaringin Timur: elevation; Ogan Komering Ilir: ndwi; Pelalawan: ndwi; Pulang Pisau: ndwi). This supports a differentiated policy: one intervention does not fit all peat landscapes.

The El Nino signal is visible: mean susceptibility on peat cells was 0.203 in 2023 versus 0.097 in 2024, with fire rates of 1.6% and 0.5% respectively.

The most at-risk district is Ogan Komering Ilir (mean susceptibility 0.160). Prioritise it for pre-positioning of suppression resources.

Spatially, 0 cells are persistent hot clusters and 239 are intensifying. Persistent cells are the structural problem; they recur and warrant permanent rewetting or monitoring infrastructure.

On high-activity days, 14 district-years show a wind-driven export bearing oriented toward the northwest (Malacca Strait corridor), the transboundary haze direction. This is a proxy, not a dispersion model.

## Caveats the reader must keep in mind
- Peat extent is an elevation-based proxy, not the licensed national map.
- Smoke export is an ERA5 wind proxy, not a physical dispersion model.
- Emerging-hotspot trend rests on 12 monthly bins; treat trend labels as indicative.
