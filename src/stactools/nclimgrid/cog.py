import os
import warnings
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import numpy as np
import rasterio
import rasterio.shutil
from rasterio.errors import NotGeoreferencedWarning
from rasterio.io import MemoryFile

from stactools.nclimgrid.constants import VARS

TRANSFORM = [0.04166667, 0.0, -124.70833333, 0.0, -0.04166667, 49.37500127]

BASE_PROFILE = {
    "compress": "deflate",
    "blocksize": 512,
    "crs": "epsg:4326",
    "nodata": np.nan,
    "count": 1,
    "transform": rasterio.Affine(*TRANSFORM),
}


def cogify(
    nc_file: str,
    cog_file: str,
    nc_index: int,
) -> None:
    warnings.simplefilter("ignore", NotGeoreferencedWarning)
    with rasterio.open(nc_file) as src:
        single_band = src.read(nc_index)

        profile = BASE_PROFILE.copy()
        profile.update(
            {
                "width": src.width,
                "height": src.height,
                "dtype": single_band.dtype,
            }
        )

        with MemoryFile() as mem:
            with mem.open(**profile, driver="GTiff") as temp:
                temp.write(single_band, 1)
                rasterio.shutil.copy(temp, cog_file, **profile, driver="COG")


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
        cogify(augmented_nc_href, cog_paths[var], nc_index)

    return cog_paths


# TODO: Make corrections to address these warnings:
# WARNING  rasterio._env:io.py:140 CPLE_NotSupported in driver GTiff does not support creation option BLOCKSIZE  # noqa
# WARNING  rasterio._env:env.py:442 CPLE_NotSupported in driver COG does not support creation option CRS  # noqa
# WARNING  rasterio._env:env.py:442 CPLE_NotSupported in driver COG does not support creation option NODATA  # noqa
# WARNING  rasterio._env:env.py:442 CPLE_NotSupported in driver COG does not support creation option COUNT  # noqa
# WARNING  rasterio._env:env.py:442 CPLE_NotSupported in driver COG does not support creation option TRANSFORM  # noqa
# WARNING  rasterio._env:env.py:442 CPLE_NotSupported in driver COG does not support creation option WIDTH  # noqa
# WARNING  rasterio._env:env.py:442 CPLE_NotSupported in driver COG does not support creation option HEIGHT  # noqa
# WARNING  rasterio._env:env.py:442 CPLE_NotSupported in driver COG does not support creation option DTYPE  # noqa
