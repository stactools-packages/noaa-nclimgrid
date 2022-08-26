import os
from typing import Dict, List, Optional

import fsspec
import numpy as np
import rasterio
import rasterio.shutil
import xarray
from rasterio.io import MemoryFile
from stactools.core.io import ReadHrefModifier
from stactools.core.utils import href_exists

from stactools.noaa_nclimgrid.constants import Variable

TRANSFORM = [0.04166667, 0.0, -124.70833333, 0.0, -0.04166667, 49.37500127]

GTIFF_PROFILE = {
    "crs": "epsg:4326",
    "width": 1385,
    "height": 596,
    "dtype": "float32",
    "nodata": np.nan,
    "count": 1,
    "transform": rasterio.Affine(*TRANSFORM),
    "driver": "GTiff",
}

COG_PROFILE = {"compress": "deflate", "blocksize": 512, "driver": "COG"}


def cog_time_slice(
    nc_href: str,
    var: str,
    cog_path: str,
    time_index: int,
) -> None:
    """Create a COG from a single timeslice of a netCDF DataArray.

    Args:
        nc_href (str): HREF to the netCDF file.
        var (str): One of 'prcp', 'tavg', 'tmax', or 'tmin'.
        cog_path (str): Destination for created COG file.
        time_index (int): index into the data timestack (netCDF DataArray).
            For daily data, the index is the day of the month. For monthly data,
            the index is the number of months since January 1895 where January
            1895 is month=1.
    """
    with fsspec.open(nc_href) as file_object:
        with xarray.open_dataset(file_object) as dataset:
            values = dataset[var].isel(time=time_index).values
            latitudes = dataset.lat.values

            if latitudes[0] < latitudes[-1]:
                values = np.flipud(values)

            with MemoryFile() as mem:
                with mem.open(**GTIFF_PROFILE) as temp:
                    temp.write(values, 1)
                    rasterio.shutil.copy(temp, cog_path, **COG_PROFILE)


def create_cogs(
    nc_hrefs: Dict[Variable, str],
    cog_paths: Dict[Variable, str],
    day: Optional[int] = None,
    month: Optional[int] = None,
    cog_check_href: Optional[str] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> List[str]:
    """Creates a prcp, tavg, tmax, and tmin COGS for a single temporal unit.

    A temporal unit is a day for daily data or a month for monthly data.

    Args:
        nc_hrefs (Dict[Variable, str]): A dictionary mapping variables to netCDF
            HREFs.
        cog_paths (Dict[Variable, str]): A dictionary mapping variables to
            target COG HREFs.
        day (Optional[int], optional): Day of month. Used to index into the
            data timestacks. Only specify for daily data.
        month (Optional[int], optional): Months since January 1895 where January
            1895 is month=1. Used to index into the data timestacks. Only
            specify for monthly data.
        cog_check_href (Optional[str]): HREF to a location to check for existing
            COG files. This can be as simple as the same local directory as in
            `cog_paths` or a remote directory, e.g., an Azure directory. New
            COGs are not created if existing COGs are found.
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        List[str]: List of created COG HREFs.
    """
    if day:
        time_index = day - 1
    elif month:
        time_index = month - 1

    for var in Variable:
        cog_exists = False
        if cog_check_href is not None:
            cog_exists = _check_cog_existence(
                cog_paths[var], cog_check_href, read_href_modifier=read_href_modifier
            )
        if cog_exists:
            cog_paths.pop(var)
        else:
            cog_time_slice(nc_hrefs[var], var, cog_paths[var], time_index)

    return list(cog_paths.values())


def _check_cog_existence(
    local_cog_path: str,
    cog_check_href: str,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> bool:
    check_href = os.path.join(cog_check_href, os.path.basename(local_cog_path))
    if read_href_modifier is not None:
        read_check_href = read_href_modifier(check_href)
    else:
        read_check_href = check_href
    return href_exists(read_check_href)


def create_cog_paths(
    nc_hrefs: Dict[Variable, str],
    cog_dir: str,
    day: Optional[int] = None,
    month: Optional[str] = None,
) -> Dict[Variable, str]:
    """Generate target local path and name for COGs.

    Args:
        nc_hrefs (Dict[Variable, str]): Dictionary of NetCDF file HREFs
        cog_dir (str): Target COG storage directory
        day (Optional[int], optional): Day of month. Only specify for daily
            data.
        month (Optional[str], optional): YYYYMM string. Only specify for
            monthly data.

    Returns:
        Dict[Variable, str]: A dictionary mapping variables to target COG HREFs.
    """
    cog_paths = {}
    if day:
        basenames = {
            var: os.path.splitext(os.path.basename(nc_hrefs[var]))[0]
            for var in Variable
        }
        cog_paths = {
            var: os.path.join(cog_dir, f"{basenames[var]}-{day:02d}.tif")
            for var in Variable
        }
    elif month:
        filenames = {var: f"nclimgrid-{var}-{month}.tif" for var in Variable}
        cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in Variable}

    return cog_paths
