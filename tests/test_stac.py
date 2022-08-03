from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

from stactools.noaa_nclimgrid import cog, stac
from stactools.noaa_nclimgrid.constants import Frequency, Variable
from tests import test_data


def test_create_monthly_items_local() -> None:
    nc_href = test_data.get_path("data-files/netcdf/monthly/nclimgrid_prcp.nc")
    with TemporaryDirectory() as cog_dir:
        items = stac.create_items(nc_href, cog_dir)
        assert len(items) == 2
        for item in items:
            item.validate()


def test_create_monthly_items_remote() -> None:
    nc_href = "https://ai4epublictestdata.blob.core.windows.net/stactools/nclimgrid/monthly/nclimgrid_prcp.nc"  # noqa
    with TemporaryDirectory() as cog_dir:
        items = stac.create_items(nc_href, cog_dir)
        assert len(items) == 2
        for item in items:
            item.validate()


def test_create_daily_items_local() -> None:
    nc_href = test_data.get_path(
        "data-files/netcdf/daily/beta/by-month/2022/01/prcp-202201-grd-prelim.nc"
    )
    with TemporaryDirectory() as cog_dir:
        items = stac.create_items(nc_href, cog_dir)
        assert len(items) == 1
        for item in items:
            item.validate()


def test_create_daily_items_remote() -> None:
    nc_href = "https://ai4epublictestdata.blob.core.windows.net/stactools/nclimgrid/daily/prcp-202201-grd-prelim.nc"  # noqa
    with TemporaryDirectory() as cog_dir:
        items = stac.create_items(nc_href, cog_dir)
        assert len(items) == 1
        for item in items:
            item.validate()


def test_create_monthly_items_new_only() -> None:
    # placeholder for testing a potential, optional callable to short-circuit
    # item creation once existing items/cogs are detected (by the callable)
    pass


def test_create_daily_items_new_only() -> None:
    pass


def test_create_single_item() -> None:
    cog_hrefs = {
        Variable.PRCP: test_data.get_path(
            "data-files/cog/monthly/nclimgrid-prcp-189501.tif"
        ),
        Variable.TAVG: test_data.get_path(
            "data-files/cog/monthly/nclimgrid-tavg-189501.tif"
        ),
        Variable.TMAX: test_data.get_path(
            "data-files/cog/monthly/nclimgrid-tmax-189501.tif"
        ),
        Variable.TMIN: test_data.get_path(
            "data-files/cog/monthly/nclimgrid-tmin-189501.tif"
        ),
    }
    item = stac.create_item(cog_hrefs)
    assert item.id == "nclimgrid-189501"
    assert len(item.assets) == 4
    item.validate()


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
        month: Optional[Dict[str, Any]] = {"idx": 1, "date": "189502"}
        cog_paths = cog.create_cogs(nc_hrefs, cog_dir, month=month)
        assert len(cog_paths) == 4


def test_read_href_modifier() -> None:
    nc_href = test_data.get_path("data-files/netcdf/monthly/nclimgrid_prcp.nc")

    did_it = False

    def read_href_modifier(href: str) -> str:
        nonlocal did_it
        did_it = True
        return href

    with TemporaryDirectory() as cog_dir:
        _ = stac.create_items(nc_href, cog_dir, read_href_modifier=read_href_modifier)
        assert did_it


def test_daily_collection() -> None:
    collection = stac.create_collection(Frequency.DAILY)
    collection_dict = collection.to_dict()
    assert collection.id == "nclimgrid-daily"
    assert "sci:doi" not in collection_dict
    assert "sci:citation" not in collection_dict
    assert "sci:publications" not in collection_dict
    assert collection_dict["item_assets"]["prcp"]["title"].startswith("Daily")


def test_monthly_collection() -> None:
    collection = stac.create_collection(Frequency.MONTHLY)
    collection_dict = collection.to_dict()
    assert collection.id == "nclimgrid-monthly"
    assert "sci:doi" in collection_dict
    assert "sci:citation" in collection_dict
    assert "sci:publications" in collection_dict
    assert collection_dict["item_assets"]["prcp"]["title"].startswith("Monthly")
