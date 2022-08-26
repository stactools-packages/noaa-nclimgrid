import os
from typing import Any, Dict, List, Optional, Tuple

import fsspec
import numpy as np
import rasterio
import rasterio.shutil
import xarray
from rasterio.io import MemoryFile
from stactools.core.io import ReadHrefModifier
from stactools.core.utils import href_exists

from stactools.noaa_nclimgrid.constants import Variable
from stactools.noaa_nclimgrid.utils import modify_href

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
) -> Tuple[Dict[Variable, str], List[str]]:
    """Creates a prcp, tavg, tmax, and tmin COG for a single temporal unit.

    A temporal unit is a day for daily data or a month for monthly data.

    Args:
        nc_hrefs (Dict[Variable, str]): A dictionary mapping variables to netCDF
            HREFs.
        cog_dir (str): Local directory path for created COGs.
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
        Tuple[Dict[Variable, str], List[str]]: A tuple consisting of:
            1. A dictionary mapping variables to COG HREFs. The HREFs may be to
                existing or newly created COGs.
            2. A list of HREFs to any newly created (not existing) COGs.
    """
    cog_hrefs = {}
    created_cog_hrefs = []
    for var in Variable:
        cog_exists = False
        if cog_check_href is not None:
            existing_cog_href = get_cog_href(
                nc_hrefs[var], var, cog_check_href, day=day, month=month
            )
            read_existing_cog_href = modify_href(existing_cog_href)
            if href_exists(read_existing_cog_href):
                cog_exists = True
                cog_hrefs[var] = existing_cog_href

        if not cog_exists:
            new_cog_path = get_cog_href(
                nc_hrefs[var], var, cog_dir, day=day, month=month
            )
            read_nc_href = modify_href(nc_hrefs[var], read_href_modifier)
            if day:
                time_index = day - 1
            elif month:
                time_index = month["idx"] - 1
            cog_time_slice(read_nc_href, var, new_cog_path, time_index)
            cog_hrefs[var] = new_cog_path
            created_cog_hrefs.append(new_cog_path)

    return cog_hrefs, created_cog_hrefs


def get_cog_href(
    nc_href: str,
    var: Variable,
    cog_dir_href: str,
    day: Optional[int] = None,
    month: Optional[Dict[str, Any]] = None,
) -> str:
    """Generates a daily or monthly COG href for a given variable, day or month,
    and directory location.

    Args:
        nc_href (str): NetCDF file HREF
        var (Variable): Variable
        cog_dir_href (str): COG location
        day (Optional[int], optional): Day of month. Used to index into the
            data timestacks. Only specify for daily data.
        month (Optional[int], optional): Months since January 1895 where January
            1895 is month=1. Used to index into the data timestacks. Only
            specify for monthly data.

    Returns:
        str: The daily or monthly COG HREF
    """
    if day:
        basename = os.path.splitext(os.path.basename(nc_href))[0]
        cog_href = os.path.join(cog_dir_href, f"{basename}-{day:02d}.tif")
    elif month:
        filename = f"nclimgrid-{var.value}-{month['date']}.tif"
        cog_href = os.path.join(cog_dir_href, filename)

    return cog_href
