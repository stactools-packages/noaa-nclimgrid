from tempfile import TemporaryDirectory

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
        month = {"idx": 1, "date": "189502"}
        for var in [Variable.PRCP, Variable.TAVG]:
            target_cog_path = cog.get_cog_href(nc_hrefs[var], var, cog_dir, month=month)
            with open(target_cog_path, "w") as _:
                pass
        cog_hrefs, created_cog_hrefs = cog.create_cogs(
            nc_hrefs, cog_dir, month=month, cog_check_href=cog_dir
        )
        assert len(cog_hrefs) == 4
        assert len(created_cog_hrefs) == 2


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
        month = {"idx": 1, "date": "189502"}
        cog_hrefs, created_cog_hrefs = cog.create_cogs(
            nc_hrefs, cog_dir, month=month, cog_check_href=cog_dir
        )
        assert len(cog_hrefs) == 4
        assert len(created_cog_hrefs) == 4
