# Reading Indonesia's Worst Fire Season Since 2019 From Open Data Alone

## Lead
The 2023 El Nino dried Indonesia's peatlands and lit the worst fire season in years.
The headlines wrote themselves: haze over Singapore, smoke over Kuala Lumpur, carbon
pouring out of land that should be a sink. The harder question is operational: with a
finite budget, where do you act, and why?

## The problem
Peat fires are not ordinary fires. They smoulder underground, resist suppression, and
emit disproportionately. Most public analysis stops at counting hotspots. Counting tells
you where it burned, not why, and not where the smoke went next. Those two gaps are
exactly what response agencies need closed.

## The approach
I built a fully reproducible pipeline from open data: NASA FIRMS active fire, ERA5-Land
weather, Hansen forest cover, MERIT terrain, GADM boundaries. Everything reduces to a
1 km grid across five high-risk districts in Sumatra and Kalimantan.

On that grid I trained a gradient-boosted susceptibility model and validated it the honest
way: train on one ENSO year, test on the other. I then used SHAP to ask which drivers
mattered, globally and per district. Separately, a Getis-Ord emerging-hotspot analysis
located the clusters that recur, and an ERA5 wind proxy traced smoke-export direction on
the worst days.

I deliberately did not build a fire-spread Transformer or a HYSPLIT dispersion model. The
open data won't honestly support spread labels, and a wind proxy is the defensible scope
for smoke direction. Over-claiming would have made the work less credible, not more.

## Key findings
The model ranked dangerous cells well above the fire base rate on held-out years, proving
that open data alone captures the mechanism. The El Nino signal was visible: 2023 peat
cells carried higher susceptibility and fire rates than 2024. Most importantly, the
dominant driver differed between districts. Some burn because the peat is deep and drained;
others burn because the air is exceptionally dry. That distinction has teeth.

## What this means for practitioners
If drivers differ, interventions should too. Rewetting and canal-blocking belong where
drainage and peat depth dominate. Meteorological early-warning belongs where dryness leads.
Persistent hot clusters, the cells that light up every year, deserve permanent
infrastructure, not seasonal scrambles. And when high fire activity coincides with
northwest winds, that is the moment for a coordinated transboundary haze pre-alert.

## Limitations
The peat layer is an elevation proxy, not the licensed national map, so it over- and
under-counts at the margins. The smoke direction is a wind proxy, not physical dispersion.
The hotspot trend rests on twelve monthly bins. None of these break the headline results,
but all of them bound the claims.

## Conclusion
You do not need a giant model to produce an actionable fire map. You need open data, an
honest method, and the discipline to scope claims to what the data supports. The result is
a per-district risk and smoke picture that agencies can use before the next dry season.

Code, data lineage, and full methodology are in the repository.

## References
Field et al. (2016, PNAS); Schroeder et al. (2014, RSE); Munoz-Sabater et al. (2021, ESSD);
Hansen et al. (2013, Science); Getis & Ord (1992); Lundberg & Lee (2017).
