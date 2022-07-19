from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

from stactools.nclimgrid import cog, stac


def test_create_items_not_latest_only() -> None:
    nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
    cog_dir = "tests/data-files/cog/monthly"

    with TemporaryDirectory() as cog_dir:
        items = stac.create_items(nc_href, cog_dir)
        assert len(items) == 2
        for item in items:
            item.validate()


def test_create_items_latest_only() -> None:
    # This should only produce Items (and COGs) for the latest data in the nc file
    # for which no COGs were found. This is, more or less, a demonstration of one way to
    # handle the in-place updates that are applied to the nc files.
    #   -> should not produce Items (or COGs) for empty placeholder data in the nc file
    #   -> should work backwards in time, checking for COG existence as the control
    #      on Item and COG creation.
    #   -> should bail once an existing set of COGs is found
    pass


def test_create_single_item() -> None:
    cog_hrefs = {
        "prcp": "tests/data-files/cog/monthly/nclimgrid-prcp-189501.tif",
        "tavg": "tests/data-files/cog/monthly/nclimgrid-tavg-189501.tif",
        "tmax": "tests/data-files/cog/monthly/nclimgrid-tmax-189501.tif",
        "tmin": "tests/data-files/cog/monthly/nclimgrid-tmin-189501.tif",
    }
    item = stac.create_item(cog_hrefs)
    assert item.id == "nclimgrid-189501"
    assert len(item.assets) == 4
    item.validate()


def test_create_cog() -> None:
    nc_hrefs = {
        "prcp": "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc",
        "tavg": "tests/data-files/netcdf/monthly/nclimgrid_tavg.nc",
        "tmax": "tests/data-files/netcdf/monthly/nclimgrid_tmax.nc",
        "tmin": "tests/data-files/netcdf/monthly/nclimgrid_tmin.nc",
    }
    with TemporaryDirectory() as cog_dir:
        month: Optional[Dict[str, Any]] = {"idx": 1, "date": "189502"}
        cog_paths = cog.create_cogs(nc_hrefs, cog_dir, month=month)
        assert len(cog_paths) == 4
