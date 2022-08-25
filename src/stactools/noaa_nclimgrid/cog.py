import os
from typing import Any, Dict, Optional

import fsspec
import numpy as np
import rasterio
import rasterio.shutil
import xarray
from rasterio.io import MemoryFile
from stactools.core.utils import href_exists
from stactools.core.io import ReadHrefModifier

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
    cog_dir: str,
    day: Optional[int] = None,
    month: Optional[Dict[str, Any]] = None,
    cog_check_href: Optional[str] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> Dict[Variable, str]:
    """Creates a prcp, tavg, tmax, and tmin COGS for a single temporal unit.

    A temporal unit is a day for daily data or a month for monthly data.

    Args:
        nc_hrefs (Dict[Variable, str]): A dictionary mapping variables (keys) to
            netCDF HREFs (values).
        cog_dir (str): Destination directory for created COGs.
        day (Optional[int], optional): Day of month. Used to index into the
            data timestacks. Only specify for daily data.
        month (Optional[Dict[str, Any]], optional): Months since January 1895
            where January 1895 is month=1. Used to index into the data
            timestacks. Only specify for monthly data.
        cog_check_href (Optional[str]): HREF to a location to check for existing
            COG files. This can be as simple as the same local directory as
            `cog_href` or a remote directory, e.g., an Azure directory. New COGs
            are not created if existing COGs are found.
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        Dict[Variable, str]: A dictionary mapping variables (keys) to COG HREFs
            (values).
    """
    cog_paths = {}
    if day:
        time_index = day - 1
        basenames = {
            var: os.path.splitext(os.path.basename(nc_hrefs[var]))[0]
            for var in Variable
        }
        cog_paths = {
            var: os.path.join(cog_dir, f"{basenames[var]}-{day:02d}.tif")
            for var in Variable
        }
    elif month:
        time_index = month["idx"] - 1
        filenames = {var: f"nclimgrid-{var}-{month['date']}.tif" for var in Variable}
        cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in Variable}

    for var in Variable:
        cog_exists = False
        if cog_check_href is not None:
            check_href = os.path.join(cog_check_href, os.path.basename(cog_paths[var]))
            if read_href_modifier is not None:
                read_check_href = read_href_modifier(check_href)
            else:
                read_check_href = check_href
            cog_exists = href_exists(read_check_href)
        if not cog_exists:
            cog_time_slice(nc_hrefs[var], var, cog_paths[var], time_index)

    return cog_paths
