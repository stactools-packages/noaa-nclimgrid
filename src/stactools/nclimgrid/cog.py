import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# from stactools.core.utils.convert import cogify
from rasterio.errors import DriverRegistrationError
from rasterio.io import MemoryFile
import rasterio

from stactools.core import utils
from stactools.nclimgrid.constants import VARS

BASE_PROFILE = {
    "compress": "deflate",
    "driver": "COG",
    "blocksize": 512,
    "epsg": 4326,
    "nodata": "nan",
    "count": 1,
}


def cogify(
    nc_file: str,
    cog_file: str,
    nc_index: int,
) -> None:
    with rasterio.open(nc_file) as src:
        single_band = src.read(nc_index)

        profile = BASE_PROFILE.copy()
        profile.update(
            {
                "width": src.width,
                "height": src.height,
                "transform": src.transform,
                "dtype": single_band.dtype,
            }
        )

        with MemoryFile() as mem:
            with mem.open(**profile, driver="GTiff") as temp:
                temp.write(single_band)
                rasterio.shutil.copy(temp, cog_file, **profile, driver="COG")


def cog_daily(nc_hrefs: Dict[str, str], cog_dir: str, day: int) -> Dict[str, str]:
    cog_paths = {}
    for var in VARS:
        basename = os.path.splitext(os.path.basename(nc_hrefs[var]))[0]
        cog_paths[var] = os.path.join(cog_dir, f"{basename}-{day:02d}.tif")

    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    augmented_nc_hrefs = {}
    for var in VARS:
        augmented_nc_hrefs[var] = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cogify(augmented_nc_hrefs[var], cog_paths[var], day)

    return cog_paths


def cog_monthly(
    nc_hrefs: Dict[str, str], cog_dir: str, month: Dict[str, str]
) -> Dict[str, str]:
    filenames = {var: f"nclimgrid-{var}-{month['date']}.tif" for var in VARS}
    cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in VARS}

    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    augmented_nc_hrefs = {}
    for var in VARS:
        augmented_nc_hrefs[var] = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cogify(augmented_nc_hrefs[var], cog_paths[var], month["idx"])

    return cog_paths


def create_cogs(
    nc_hrefs: Dict[str, str],
    cog_dir: str,
    day: Optional[int] = None,
    month: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    cog_paths = {}
    if day:
        nc_index = day
        for var in VARS:
            basename = os.path.splitext(os.path.basename(nc_hrefs[var]))[0]
            cog_paths[var] = os.path.join(cog_dir, f"{basename}-{day:02d}.tif")
    else:
        nc_index = month["idx"]
        filenames = {var: f"nclimgrid-{var}-{month['date']}.tif" for var in VARS}
        cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in VARS}

    
    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    augmented_nc_hrefs = {}
    for var in VARS:
        augmented_nc_hrefs[var] = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cogify(augmented_nc_hrefs[var], cog_paths[var], nc_index)
