import os
from typing import Any, Dict
from urllib.parse import urlparse

from stactools.core.utils.convert import cogify

from stactools.nclimgrid.constants import VARS


def cog_daily(nc_hrefs: Dict[str, str], cog_dir: str, day: int) -> Dict[str, str]:
    cog_paths = {}
    for var in VARS:
        basename = os.path.splitext(os.path.basename(nc_hrefs[var]))[0]
        cog_paths[var] = os.path.join(cog_dir, f"{basename}-{day:02d}.tif")

    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    augmented_nc_hrefs = {}
    profile = {"crs": "epsg:4326", "nodata": "nan"}
    for var in VARS:
        augmented_nc_hrefs[var] = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cogify(augmented_nc_hrefs[var], cog_paths[var], day, profile)

    return cog_paths


def cog_monthly(
    nc_hrefs: Dict[str, str], cog_dir: str, month: Dict[str, Any]
) -> Dict[str, str]:
    filenames = {var: f"nclimgrid-{var}-{month['date']}.tif" for var in VARS}
    cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in VARS}

    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    augmented_nc_hrefs = {}
    profile = {"crs": "epsg:4326", "nodata": "nan"}
    for var in VARS:
        augmented_nc_hrefs[var] = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cogify(augmented_nc_hrefs[var], cog_paths[var], month["idx"], profile)

    return cog_paths
