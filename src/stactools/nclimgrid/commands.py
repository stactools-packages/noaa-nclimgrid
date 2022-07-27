import logging
import os

import click
from click import Command, Group

from stactools.nclimgrid import stac

logger = logging.getLogger(__name__)


def create_nclimgrid_command(cli: Group) -> Command:
    """Creates the stactools-nclimgrid command line utility."""

    @cli.group(
        "nclimgrid",
        short_help=("Commands for working with stactools-nclimgrid"),
    )
    def nclimgrid() -> None:
        pass

    # @nclimgrid.command(
    #     "create-collection",
    #     short_help="Creates a STAC collection",
    # )
    # @click.argument("destination")
    # def create_collection_command(destination: str) -> None:
    #     """Creates a STAC Collection

    #     Args:
    #         destination (str): An HREF for the Collection JSON
    #     """
    #     collection = stac.create_collection()

    #     collection.set_self_href(destination)

    #     collection.save_object()

    #     return None

    @nclimgrid.command("create-items", short_help="Creates STAC Items")
    @click.argument("INFILE")
    @click.argument("COGDIR")
    @click.argument("ITEMDIR")
    def create_item_command(infile: str, cogdir: str, itemdir: str) -> None:
        """Creates COGs and STAC Items for each day or month in the daily or
        monthly netCDF infile.

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
