import logging
import os
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

import click
from click import Command, Group
from pystac import CatalogType, Item
from stactools.core.copy import move_asset_file_to_item

from stactools.noaa_nclimgrid import stac
from stactools.noaa_nclimgrid.constants import Variable
from stactools.noaa_nclimgrid.utils import data_frequency

logger = logging.getLogger(__name__)


def create_noaa_nclimgrid_command(cli: Group) -> Command:
    """Creates the stactools-noaa-nclimgrid command line utility."""

    @cli.group(
        "noaa-nclimgrid",
        short_help=("Commands for working with stactools-noaa-nclimgrid"),
    )
    def noaa_nclimgrid() -> None:
        pass

    @noaa_nclimgrid.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("INFILE")
    @click.argument("OUTDIR")
    @click.option(
        "-n",
        "--nc_assets",
        is_flag=True,
        default=False,
        show_default=True,
        help="Include source netCDF file assets in Items",
    )
    def create_collection_command(infile: str, outdir: str, nc_assets: bool) -> None:
        """Creates a STAC Collection with Items generated from the HREFs listed
        in INFILE. COGs are also generated and stored alongside the Items.

        The INFILE should contain only Daily or only monthly HREFs. Only a
        single HREF to a single variable (prcp, tavg, tmax, or tmin) should be
        listed in the INFILE for each group of netCDF files.

        \b
        Args:
            infile (str): Text file containing one HREF to a netCDF file per
                line.
            outdir (str): Directory that will contain the collection.
            nc_assets (bool): Flag to include source netCDF file assets in
                created Items. Default is False.
        """
        with open(infile) as f:
            hrefs = [os.path.abspath(line.strip()) for line in f.readlines()]

        items: List[Item] = []
        frequency = data_frequency(hrefs[0])
        with TemporaryDirectory() as cog_dir:
            for href in hrefs:
                temp_items, _ = stac.create_items(href, cog_dir, nc_assets=nc_assets)
                items.extend(temp_items)

            collection = stac.create_collection(frequency, nc_assets)
            collection.catalog_type = CatalogType.SELF_CONTAINED
            collection.set_self_href(
                os.path.join(outdir, f"{frequency}/collection.json")
            )

            collection.add_items(items)
            collection.update_extent_from_items()

            # Only move the COGs (not the source netCDFs) next to the Items
            for item in collection.get_all_items():
                for var in Variable:
                    new_href = move_asset_file_to_item(
                        item, item.assets[var].href, ignore_conflicts=True
                    )
                    item.assets[var].href = new_href

            collection.make_all_asset_hrefs_relative()

        collection.validate_all()
        collection.save()

        return None

    @noaa_nclimgrid.command("create-items", short_help="Creates STAC Items")
    @click.argument("INFILE")
    @click.argument("COGDIR")
    @click.argument("ITEMDIR")
    @click.option(
        "-n",
        "--nc_assets",
        is_flag=True,
        default=False,
        show_default=True,
        help="Include source netCDF file assets in Items",
    )
    @click.option(
        "-c",
        "--cog-check-href",
        type=str,
        help="HREF to directory to check for existing COGs",
    )
    @click.option(
        "-d",
        "--daily-range",
        nargs=2,
        type=int,
        help="Desired start and end day of month for daily data",
    )
    def create_items_command(
        infile: str,
        cogdir: str,
        itemdir: str,
        nc_assets: bool,
        cog_check_href: Optional[str] = None,
        daily_range: Optional[Tuple[int, int]] = None,
    ) -> None:
        """Creates COGs and STAC Items for each day or month in the daily or
        monthly netCDF INFILE.

        \b
        Args:
            infile (str): HREF to a netCDF file for one of the four variables:
                prcp, tavg, tmax, and tmin. The netCDF files for the remaining
                three variable must exist alongside `infile`.
            cogdir (str): Directory that will contain the COGs.
            itemdir (str): Directory that will contain the STAC Items.
            nc_assets (bool): Flag to include source netCDF file assets in
                created Items. Default is False.
            cog_check_href (Optional[str]): HREF to a location to check for
                existing COG files. New COGs are not created if existing COGs
                are found. The `cog_check_href` can simply be the same local
                directory as `cogdir` or a remote directory, e.g., an Azure
                blob storage container.
            daily_range (Optional[Tuple[int, int]]): Optional start and end day
                of month for daily data
        """
        items, _ = stac.create_items(
            infile,
            cogdir,
            nc_assets=nc_assets,
            cog_check_href=cog_check_href,
            daily_range=daily_range,
        )
        for item in items:
            item_path = os.path.join(itemdir, f"{item.id}.json")
            item.set_self_href(item_path)
            item.make_asset_hrefs_relative()
            item.validate()
            item.save_object(include_self_link=False)

        return None

    return noaa_nclimgrid
