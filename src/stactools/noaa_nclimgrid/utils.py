import operator
import os
from typing import Any, Dict, List, Optional, Tuple

import fsspec
import xarray
from dateutil import parser
from pystac import MediaType
from pystac.utils import datetime_to_str
from stactools.core.io import ReadHrefModifier

from stactools.noaa_nclimgrid import constants
from stactools.noaa_nclimgrid.constants import Frequency, Variable


def modify_href(
    href: str, read_href_modifier: Optional[ReadHrefModifier] = None
) -> str:
    """Modify an HREF with, for example, a token signature.

    Args:
        href (str): The HREF to be modified
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        str: The modified HREF.
    """
    if read_href_modifier:
        return read_href_modifier(href)
    else:
        return href


def nc_href_dict(nc_href: str) -> Dict[Variable, str]:
    """Creates a dictionary mapping variables to netCDF HREFs.

    Variables refers to one of 'prcp', 'tavg', 'tmax', or 'tmin': :py:class:`Variable`.

    Args:
        nc_href (str): HREF to a netCDF containing data from a single variable.

    Returns:
        Dict[Variable, str]: A dictionary mapping variables to netCDF HREFs.
    """
    frequency = Frequency.from_href(nc_href)

    base, filename = os.path.split(nc_href)

    if frequency == Frequency.DAILY:
        suffix = filename[4:]
        filenames = {var: f"{var}{suffix}" for var in Variable}
    else:
        filenames = {var: f"nclimgrid_{var}{filename[14:]}" for var in Variable}

    href_dict = {var: os.path.join(base, f) for var, f in filenames.items()}

    return href_dict


def day_indices(
    nc_prcp_href: str,
    day_range: Optional[Tuple[int, int]] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> List[int]:
    """Creates a list of days, in descending order, with valid precipitation
    data in a daily 'prcp' netCDF file.

    The passed HREF must contain precipitation data. Daily netCDF precipitation
    files for the current month contain 'fill' data (negative values) for those
    days that do not yet contain data. This method detects the fill data and
    does not include those days in the returned list.

    Args:
        nc_prcp_href (str): HREF to daily netCDF precipitation file.
        day_range (Optional[Tuple[int, int]]): An optional tuple of desired
            start and end day of month. For example: (<start_day_of_month>,
            <end_day_of_month>).
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        List[int]: List of days, in descending order, that have valid data.
    """
    if Variable.PRCP not in os.path.basename(nc_prcp_href):
        raise ValueError(f"'{Variable.PRCP}' not detected in HREF: {nc_prcp_href}")

    read_nc_prcp_href = modify_href(nc_prcp_href, read_href_modifier=read_href_modifier)
    with fsspec.open(read_nc_prcp_href) as fobj:
        with xarray.open_dataset(fobj) as dataset:
            min_prcp = dataset.prcp.min(dim=("lat", "lon"), skipna=True).values
            days = sum(min_prcp >= 0)

    if day_range:
        if day_range[0] < 1:
            raise ValueError("Minimum day in 'day_range' must be >= 1")
        elif day_range[1] > days:
            raise ValueError(
                "Maximum day in 'day_range' is posterior to available data"
            )
        elif day_range[0] > day_range[1]:
            raise ValueError(
                "The second element of 'day_range' must be >= to the first element."
            )
        else:
            day_start = day_range[0] if day_range[0] > 1 else 1
            day_end = day_range[1] if day_range[1] < days else days
    else:
        day_start = 1
        day_end = days

    return list(range(day_end, day_start - 1, -1))


def month_indices(
    nc_href: str,
    month_range: Optional[Tuple[str, str]] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> List[Dict[str, Any]]:
    """Creates a list of dictionaries, where each dictionary contains an index
    into the monthly netCDF data timestack and a corresponding yyyymm string
    indicating the year and month.

    Args:
        nc_href (str): HREF to a monthly netCDF file.
        month_range (Optional[Tuple[str, str]]): An optional tuple of desired
            start and end YYYYMM date strings. For example: (<start_YYYYMM>,
            <end_YYYYMM>).
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        List[Dict[str, Any]]: List of dictionaries with indices into the NetCDF
            timestack and corresponding YYYYMM date strings for each time slice.
    """
    read_nc_href = modify_href(nc_href, read_href_modifier=read_href_modifier)
    with fsspec.open(read_nc_href) as fobj:
        with xarray.open_dataset(fobj) as ds:
            years = ds.time.dt.year.data.tolist()
            months = ds.time.dt.month.data.tolist()

    idx_month: List[Dict[str, Any]] = []
    for idx, (year, month) in enumerate(zip(years, months), start=1):
        idx_month.append({"idx": idx, "date": f"{year}{month:02d}"})

    if month_range:
        idx_month.sort(key=operator.itemgetter("idx"))
        if int(month_range[0]) < int(idx_month[0]["date"]):
            raise ValueError(
                f"'month_range' start YYYYMM ({month_range[0]}) is prior to available data"
            )
        elif int(month_range[1]) > int(idx_month[-1]["date"]):
            raise ValueError(
                f"'month_range' start YYYYMM ({month_range[1]}) is posterior to available data"
            )
        elif int(month_range[0]) > int(month_range[1]):
            raise ValueError(
                "The second element of 'month_range' must be >= to the first element."
            )
        else:
            idx_month = [
                m
                for m in idx_month
                if int(month_range[0]) <= int(m["date"]) <= int(month_range[1])
            ]

    idx_month.sort(key=operator.itemgetter("idx"), reverse=True)

    return idx_month


def cog_asset_dict(frequency: Frequency, var: Variable) -> Dict[str, Any]:
    """Returns a COG asset, less the HREF, in dictionary form.

    Args:
        var (Variable):  One of 'prcp', 'tavg', 'tmax', or 'tmin'.

    Returns:
        Dict[str, Any]: A partial dictionary of STAC Asset components.
    """
    return {
        "type": MediaType.COG,
        "roles": constants.COG_ROLES,
        "title": f"{frequency.capitalize()} {constants.COG_ASSET_TITLES[var]}",
        "raster:bands": constants.COG_RASTER_BANDS[var],
    }


def nc_asset_dict(frequency: Frequency, var: Variable) -> Dict[str, Any]:
    """Returns a netCDF asset, less the HREF, in dictionary form.

    Args:
        var (Variable):  One of 'prcp', 'tavg', 'tmax', or 'tmin'.

    Returns:
        Dict[str, Any]: A partial dictionary of STAC Asset components.
    """
    return {
        "type": constants.NETCDF_MEDIA_TYPE,
        "roles": constants.NETCDF_ROLES,
        "title": f"{frequency.capitalize()} {constants.NETCDF_ASSET_TITLES[var]}",
    }


def nc_creation_date_dict(
    nc_hrefs: Dict[Variable, str], read_href_modifier: Optional[ReadHrefModifier] = None
) -> Dict[Variable, str]:
    """Returns a dictionary mapping variables to netCDF file creation dates.

    Args:
        nc_hrefs (Dict[Variable, str]): A dictionary mapping variables to netCDF
            HREFS.
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        Dict[Variable, str]: A dictionary mapping variables to netCDF file
            creation times.
    """
    nc_creation_dates: Dict[Variable, str] = {}
    for var in Variable:
        read_nc_href = modify_href(nc_hrefs[var], read_href_modifier=read_href_modifier)
        with fsspec.open(read_nc_href) as fobj:
            with xarray.open_dataset(fobj) as ds:
                nc_creation_dates[var] = datetime_to_str(
                    parser.parse(ds.attrs["date_created"])
                )
    return nc_creation_dates
