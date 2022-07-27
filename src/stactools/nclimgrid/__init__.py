import stactools.core
from stactools.cli.registry import Registry

from stactools.nclimgrid.stac import create_collection, create_items

__all__ = ["create_items", "create_collection"]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.nclimgrid import commands

    registry.register_subcommand(commands.create_nclimgrid_command)


__version__ = "0.1.0"
