import operator
import os
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import xarray

from stactools.nclimgrid.constants import VARS


def nc_href_dict(nc_href: str) -> Tuple[Dict[str, str], bool]:
    base, filename = os.path.split(nc_href)

    if "nclimgrid" in filename:  # monthly
        filenames = {var: f"{filename[0:10]}{var}{filename[14:]}" for var in VARS}
        daily = False
    elif "ncdd" in filename:  # daily pre-1970
        filenames = {var: filename for var in VARS}
        daily = True
    else:  # daily 1970-onward
        suffix = filename[4:]
        filenames = {var: f"{var}{suffix}" for var in VARS}
        daily = True

    href_dict = {var: os.path.join(base, f) for var, f in filenames.items()}

    return (href_dict, daily)


def day_indices(nc_href: str) -> List[int]:
    href = nc_href
    if urlparse(nc_href).scheme.startswith("http"):
        href += "#mode=bytes"

    with xarray.open_dataset(href) as dataset:
        min_prcp = dataset.prcp.min(dim=("lat", "lon"), skipna=True).values
        days = sum(min_prcp >= 0)

    return list(range(days, 0, -1))


def month_indices(nc_href: str) -> List[Dict[str, Any]]:
    href = nc_href
    if urlparse(nc_href).scheme.startswith("http"):
        href += "#mode=bytes"

    with xarray.open_dataset(href) as ds:
        years = ds.time.dt.year.data.tolist()
        months = ds.time.dt.month.data.tolist()

    idx_month = []
    for idx, (year, month) in enumerate(zip(years, months), start=1):
        idx_month.append({"idx": idx, "date": f"{year}{month:02d}"})

    idx_month.sort(key=operator.itemgetter("idx"), reverse=True)

    return idx_month
