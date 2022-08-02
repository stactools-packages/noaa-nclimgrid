import operator
import os
from typing import Any, Dict, List

import fsspec
import xarray
from pystac import MediaType

from stactools.nclimgrid.constants import (
    ASSET_TITLES,
    RASTER_BANDS,
    Frequency,
    Variable,
)


def data_frequency(href: str) -> Frequency:
    """Determine if data is 'monthly' or 'daily' from the passed HREF.

    Args:
        href (str): HREF to a NClimGrid netCDF or COG file.

    Returns:
        Frequency: Enum of 'monthly' or 'daily'.
    """
    basename = os.path.splitext(os.path.basename(href))[0]
    frequency = (
        Frequency.MONTHLY if basename.startswith("nclimgrid") else Frequency.DAILY
    )
    return frequency


def nc_href_dict(nc_href: str) -> Dict[Variable, str]:
    """Creates a dictionary mapping variables to netCDF HREFs.

    Variables refers to one of 'prcp', 'tavg', 'tmax', or 'tmin': :py:class:`Variable`.

    Args:
        nc_href (str): HREF to a netCDF containing data from a single variable.

    Returns:
        Dict[Variable, str]: A dictionary mapping variables to netCDF HREFs.
    """
    frequency = data_frequency(nc_href)

    base, filename = os.path.split(nc_href)

    if frequency == Frequency.DAILY:
        suffix = filename[4:]
        filenames = {var: f"{var}{suffix}" for var in Variable}
    else:
        filenames = {var: f"nclimgrid_{var}{filename[14:]}" for var in Variable}

    href_dict = {var: os.path.join(base, f) for var, f in filenames.items()}

    return href_dict


def day_indices(nc_prcp_href: str) -> List[int]:
    """Creates a list of days, in descending order, with valid precipitation
    data in a daily 'prcp' netCDF file.

    The passed HREF must contain precipitation data. Daily netCDF precipitation
    files for the current month contain 'fill' data (negative values) for those
    days that do not yet contain data. This method detects the fill data and
    does not include those days in the returned list.

    Args:
        nc_prcp_href (str): HREF to daily netCDF precipitation file.

    Returns:
        List[int]: List of days that have valid data.
    """
    if Variable.PRCP not in os.path.basename(nc_prcp_href):
        raise ValueError(f"'{Variable.PRCP}' not detected in HREF: {nc_prcp_href}")

    with fsspec.open(nc_prcp_href) as fobj:
        with xarray.open_dataset(fobj) as dataset:
            min_prcp = dataset.prcp.min(dim=("lat", "lon"), skipna=True).values
            days = sum(min_prcp >= 0)

    return list(range(days, 0, -1))


def month_indices(nc_href: str) -> List[Dict[str, Any]]:
    """Creates a list of dictionaries, where each dictionary contains an index
    into the monthly netCDF data timestack and a corresponding yyyymm string
    indicating the year and month.

    Args:
        nc_href (str): HREF to a monthly netCDF file.

    Returns:
        List[Dict[str, Any]]: List of dictionaries with index and timeslice
            information.
    """
    with fsspec.open(nc_href) as fobj:
        with xarray.open_dataset(fobj) as ds:
            years = ds.time.dt.year.data.tolist()
            months = ds.time.dt.month.data.tolist()

    idx_month = []
    for idx, (year, month) in enumerate(zip(years, months), start=1):
        idx_month.append({"idx": idx, "date": f"{year}{month:02d}"})

    idx_month.sort(key=operator.itemgetter("idx"), reverse=True)

    return idx_month


def asset_dict(frequency: str, var: Variable) -> Dict[str, Any]:
    """Returns a COG asset, less the HREF, in dictionary form.

    Args:
        frequency (str): One of 'daily' or 'monthly'.
        var (str): One of 'prcp', 'tavg', 'tmax', or 'tmin'.

    Returns:
        Dict[str, Any]: A partial dictionary of STAC Asset components.
    """
    return {
        "media_type": MediaType.COG,
        "roles": ["data"],
        "title": f"{frequency.capitalize()} {ASSET_TITLES[var]}",
        "raster:bands": RASTER_BANDS[var],
    }
