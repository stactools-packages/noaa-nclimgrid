import logging
import os
from tempfile import TemporaryDirectory

import click
from click import Command, Group
from pystac import CatalogType
from stactools.core.copy import move_all_assets

from stactools.nclimgrid import stac
from stactools.nclimgrid.utils import data_frequency

logger = logging.getLogger(__name__)


def create_nclimgrid_command(cli: Group) -> Command:
    """Creates the stactools-nclimgrid command line utility."""

    @cli.group(
        "nclimgrid",
        short_help=("Commands for working with stactools-nclimgrid"),
    )
    def nclimgrid() -> None:
        pass

    @nclimgrid.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("INFILE")
    @click.argument("OUTDIR")
    def create_collection_command(infile: str, outdir: str) -> None:
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
        """
        with open(infile) as f:
            hrefs = [os.path.abspath(line.strip()) for line in f.readlines()]

        items = []
        frequency = data_frequency(hrefs[0]).value
        with TemporaryDirectory() as cog_dir:
            for href in hrefs:
                temp_items = stac.create_items(href, cog_dir)
                items.extend(temp_items)

            collection = stac.create_collection(frequency)
            collection.catalog_type = CatalogType.SELF_CONTAINED
            collection.set_self_href(
                os.path.join(outdir, f"{frequency}/collection.json")
            )

            collection.add_items(items)
            collection.update_extent_from_items()
            move_all_assets(
                collection,
            )

        collection.validate_all()
        collection.save()

        return None

    @nclimgrid.command("create-items", short_help="Creates STAC Items")
    @click.argument("INFILE")
    @click.argument("COGDIR")
    @click.argument("ITEMDIR")
    def create_items_command(infile: str, cogdir: str, itemdir: str) -> None:
        """Creates COGs and STAC Items for each day or month in the daily or
        monthly netCDF INFILE.

        \b
        Args:
            infile (str): HREF to a netCDF file for one of the four variables:
                prcp, tavg, tmax, and tmin. The netCDF files for the remaining
                three variable must exist alongside `infile`.
            cogdir (str): Directory that will contain the COGs.
            itemdir (str): Directory that will contain the STAC Items
        """
        items = stac.create_items(infile, cogdir)
        for item in items:
            item_path = os.path.join(itemdir, f"{item.id}.json")
            item.set_self_href(item_path)
            item.make_asset_hrefs_relative()
            item.validate()
            item.save_object(include_self_link=False)

        return None

    return nclimgrid
