import glob
from tempfile import TemporaryDirectory
from typing import Callable, List

import pystac
from click import Command, Group
from stactools.testing.cli_test import CliTestCase

from stactools.nclimgrid.commands import create_nclimgrid_command


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_nclimgrid_command]

    # def test_create_collection(self) -> None:
    #     with TemporaryDirectory() as tmp_dir:
    #         # Run your custom create-collection command and validate

    #         # Example:
    #         destination = os.path.join(tmp_dir, "collection.json")

    #         result = self.run_command(f"ephemeralcmd create-collection {destination}")

    #         assert result.exit_code == 0, "\n{}".format(result.output)

    #         jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
    #         assert len(jsons) == 1

    #         collection = pystac.read_file(destination)
    #         assert collection.id == "my-collection-id"
    #         # assert collection.other_attr...

    #         collection.validate()

    def test_create_monthly_items(self) -> None:
        nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
        with TemporaryDirectory() as tmp_dir:
            cmd = f"nclimgrid create-items {nc_href} {tmp_dir} {tmp_dir}"
            self.run_command(cmd)

            cog_files = glob.glob(f"{tmp_dir}/*tif")
            assert len(cog_files) == 8
            item_files = glob.glob(f"{tmp_dir}/*.json")
            assert len(item_files) == 2

            for item_file in item_files:
                item = pystac.read_file(item_file)
                item.validate()

    def test_create_daily_items(self) -> None:
        nc_href = "tests/data-files/netcdf/daily/beta/by-month/2022/01/prcp-202201-grd-prelim.nc"  # noqa
        with TemporaryDirectory() as tmp_dir:
            cmd = f"nclimgrid create-items {nc_href} {tmp_dir} {tmp_dir}"
            self.run_command(cmd)

            cog_files = glob.glob(f"{tmp_dir}/*tif")
            assert len(cog_files) == 4
            item_files = glob.glob(f"{tmp_dir}/*.json")
            assert len(item_files) == 1

            for item_file in item_files:
                item = pystac.read_file(item_file)
                item.validate()
