from stactools.nclimgrid import utils


def test_day_indices_local() -> None:
    nc_href = "tests/data-files/netcdf/daily/beta/by-month/2022/01/prcp-202201-grd-prelim.nc"  # noqa
    idx = utils.day_indices(nc_href)
    assert len(idx) == 1


def test_day_indices_remote() -> None:
    nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily/beta/by-month/2022/06/prcp-202206-grd-scaled.nc"  # noqa
    idx = utils.day_indices(nc_href)
    assert len(idx) == 30


def test_month_indices_local() -> None:
    nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
    idx = utils.month_indices(nc_href)
    assert len(idx) == 2


def test_month_indices_remote() -> None:
    nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-monthly/nclimgrid_prcp.nc"  # noqa
    idx = utils.month_indices(nc_href)
    assert len(idx) == 1530
