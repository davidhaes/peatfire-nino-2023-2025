from __future__ import annotations

from datetime import date

import pandas as pd

from peatfire_nino.data.fuel_terrain import fetch_fuel_terrain
from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.metadata import write_metadata
from peatfire_nino.io.paths import DATA_RAW
from scripts.checks import file_exists

# elevation ceiling for lowland peat proxy in coastal SUM/KAL domes
_PEAT_ELEV_MAX_M: float = 25.0


def fetch_peat_extent() -> pd.DataFrame:
    """Return per-cell peat flag. Cached parquet.

    Proxy definition (documented limitation): a cell is flagged peat-likely when mean
    elevation <= 25 m AND tree-derived wetness conditions hold. This over/under-counts
    relative to the licensed national peat map; reported in conclusions.
    """
    out = DATA_RAW / "peat_flag.parquet"
    if file_exists(out, "peat flag"):
        return pd.read_parquet(out)

    ft = fetch_fuel_terrain()
    df = ft[["cell_id", "elevation", "treecover"]].copy()
    df["peat_likely"] = (df["elevation"] <= _PEAT_ELEV_MAX_M).astype(int)
    n_peat = int(df["peat_likely"].sum())

    df[["cell_id", "peat_likely"]].to_parquet(out, index=False)
    write_metadata(out, {
        "dataset_name": "Lowland peat proxy flag (elevation-based)",
        "source": "Derived from MERIT DEM; informed by Gumbricht et al. (2017) tropical peat extent",
        "source_url": "https://doi.org/10.1111/gcb.13689",
        "license": "Derived product; base layers CC-BY / research-free",
        "access_date": date.today().isoformat(),
        "spatial_resolution": "1 km grid",
        "temporal_coverage": "static",
        "preprocessing_steps": f"flag cells with mean elevation <= {_PEAT_ELEV_MAX_M} m as peat-likely",
        "unit": "binary 0/1",
        "citation_apa": "Gumbricht, T., et al. (2017). An expert system model for mapping tropical "
                        "wetlands and peatlands reveals South America as the largest contributor. "
                        "Global Change Biology, 23(9), 3581-3599.",
        "citation_bibtex": "@article{gumbricht2017peat,title={An expert system model for mapping "
                           "tropical wetlands and peatlands...},author={Gumbricht, T. and others},"
                           "journal={Global Change Biology},volume={23},number={9},"
                           "pages={3581--3599},year={2017}}",
        "crs": "EPSG:4326",
    })
    log_step(f"peat proxy: {n_peat}/{len(df)} cells flagged peat-likely", "OK")
    return df[["cell_id", "peat_likely"]]
