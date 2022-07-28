import operator
import os
from typing import Any, Dict, List

import fsspec
import xarray
from pystac import MediaType

from stactools.nclimgrid.constants import ASSET_TITLES, RASTER_BANDS, VARS, Frequency


def data_frequency(href: str) -> Frequency:
    basename = os.path.splitext(os.path.basename(href))[0]
    frequency = (
        Frequency.MONTHLY if basename.startswith("nclimgrid") else Frequency.DAILY
    )
    return frequency


def nc_href_dict(nc_href: str) -> Dict[str, str]:
    frequency = data_frequency(nc_href)
    base, filename = os.path.split(nc_href)

    if frequency == Frequency.DAILY:
        suffix = filename[4:]
        filenames = {var: f"{var}{suffix}" for var in VARS}
    else:
        filenames = {var: f"nclimgrid_{var}{filename[14:]}" for var in VARS}

    href_dict = {var: os.path.join(base, f) for var, f in filenames.items()}

    return href_dict


def day_indices(nc_href: str) -> List[int]:
    with fsspec.open(nc_href) as fobj:
        with xarray.open_dataset(fobj) as dataset:
            min_prcp = dataset.prcp.min(dim=("lat", "lon"), skipna=True).values
            days = sum(min_prcp >= 0)

    return list(range(days, 0, -1))


def month_indices(nc_href: str) -> List[Dict[str, Any]]:
    with fsspec.open(nc_href) as fobj:
        with xarray.open_dataset(fobj) as ds:
            years = ds.time.dt.year.data.tolist()
            months = ds.time.dt.month.data.tolist()

    idx_month = []
    for idx, (year, month) in enumerate(zip(years, months), start=1):
        idx_month.append({"idx": idx, "date": f"{year}{month:02d}"})

    idx_month.sort(key=operator.itemgetter("idx"), reverse=True)

    return idx_month


def asset_dict(frequency: str, var: str) -> Dict[str, Any]:
    return {
        "media_type": MediaType.COG,
        "roles": ["data"],
        "title": f"{frequency.capitalize()} {ASSET_TITLES[var]}",
        "raster:bands": RASTER_BANDS[var],
    }
