from tempfile import TemporaryDirectory
from typing import Optional

from stactools.noaa_nclimgrid import cog
from stactools.noaa_nclimgrid.constants import Variable
from tests import test_data


def test_check_cog_existence() -> None:
    nc_hrefs = {
        Variable.PRCP: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_prcp.nc"
        ),
        Variable.TAVG: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_tavg.nc"
        ),
        Variable.TMAX: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_tmax.nc"
        ),
        Variable.TMIN: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_tmin.nc"
        ),
    }
    with TemporaryDirectory() as cog_dir:
        month_idx: Optional[int] = 1
        month_date: Optional[str] = "189502"
        target_cog_paths = cog.create_cog_paths(nc_hrefs, cog_dir, month=month_date)
        for var in [Variable.PRCP, Variable.TAVG]:
            with open(target_cog_paths[var], "w") as _:
                pass
        created_cog_paths = cog.create_cogs(
            nc_hrefs, target_cog_paths, month=month_idx, cog_check_href=cog_dir
        )
        assert len(created_cog_paths) == 2


def test_create_cogs() -> None:
    nc_hrefs = {
        Variable.PRCP: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_prcp.nc"
        ),
        Variable.TAVG: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_tavg.nc"
        ),
        Variable.TMAX: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_tmax.nc"
        ),
        Variable.TMIN: test_data.get_path(
            "data-files/netcdf/monthly/nclimgrid_tmin.nc"
        ),
    }
    with TemporaryDirectory() as cog_dir:
        month_idx: Optional[int] = 1
        month_date: Optional[str] = "189502"
        target_cog_paths = cog.create_cog_paths(nc_hrefs, cog_dir, month=month_date)
        created_cog_paths = cog.create_cogs(nc_hrefs, target_cog_paths, month=month_idx)
        assert len(created_cog_paths) == 4
