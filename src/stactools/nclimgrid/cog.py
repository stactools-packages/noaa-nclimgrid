import os
from typing import Any, Dict, Optional

import fsspec
import numpy as np
import rasterio
import rasterio.shutil
import xarray
from rasterio.io import MemoryFile

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


def cog_time_slice(
    nc_href: str,
    var: str,
    cog_path: str,
    time_index: int,
) -> None:
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
    nc_hrefs: Dict[str, str],
    cog_dir: str,
    day: Optional[int] = None,
    month: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    cog_paths = {}
    if day:
        time_index = day - 1
        basenames = {
            var: os.path.splitext(os.path.basename(nc_hrefs[var]))[0] for var in VARS
        }
        cog_paths = {
            var: os.path.join(cog_dir, f"{basenames[var]}-{day:02d}.tif")
            for var in VARS
        }
    elif month:
        time_index = month["idx"] - 1
        filenames = {var: f"nclimgrid-{var}-{month['date']}.tif" for var in VARS}
        cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in VARS}

    for var in VARS:
        cog_time_slice(nc_hrefs[var], var, cog_paths[var], time_index)

    return cog_paths
