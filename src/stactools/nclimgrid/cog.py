import os
import warnings
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import numpy as np
import rasterio
import rasterio.shutil
from rasterio.errors import NotGeoreferencedWarning
from rasterio.io import MemoryFile
import fsspec
import xarray

from stactools.nclimgrid.constants import VARS

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


def cog_nc_band(
    nc_href: str,
    var: str,
    cog_file: str,
    time_index: int,
) -> None:
    with fsspec.open(nc_href) as file_object:
        with xarray.open_dataset(file_object) as dataset:
            values = dataset[var].isel(time=time_index-1).values
            latitudes = dataset.lat.values

            if latitudes[0] < latitudes[-1]:
                values = np.flipud(values)

            with MemoryFile() as mem:
                with mem.open(**GTIFF_PROFILE) as temp:
                    temp.write(values, 1)
                    rasterio.shutil.copy(temp, cog_file, **COG_PROFILE)


def create_cogs(
    nc_hrefs: Dict[str, str],
    cog_dir: str,
    day: Optional[int] = None,
    month: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    cog_paths = {}
    if day:
        nc_index = day
        basenames = {
            var: os.path.splitext(os.path.basename(nc_hrefs[var]))[0] for var in VARS
        }
        cog_paths = {
            var: os.path.join(cog_dir, f"{basenames[var]}-{day:02d}.tif")
            for var in VARS
        }
    elif month:
        nc_index = month["idx"]
        filenames = {var: f"nclimgrid-{var}-{month['date']}.tif" for var in VARS}
        cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in VARS}

    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    for var in VARS:
        augmented_nc_href = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cog_nc_band(augmented_nc_href, cog_paths[var], nc_index)

    return cog_paths


# nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-monthly/nclimgrid_prcp.nc"

# nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily/beta/by-month/2021/01/prcp-202101-grd-scaled.nc"
# nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily/beta/by-month/1951/01/prcp-195101-grd-scaled.nc"

cog_nc_band(nc_href, "test_https_monthly.tif", 1)