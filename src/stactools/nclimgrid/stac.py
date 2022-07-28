import logging
import os
from calendar import monthrange
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import stactools.core.create
from pystac import Asset, Collection, Item
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.scientific import ScientificExtension
from pystac.utils import make_absolute_href
from stactools.core.io import ReadHrefModifier

from stactools.nclimgrid import constants
from stactools.nclimgrid.cog import create_cogs
from stactools.nclimgrid.constants import VARS, Frequency
from stactools.nclimgrid.utils import (
    asset_dict,
    data_frequency,
    day_indices,
    month_indices,
    nc_href_dict,
)

logger = logging.getLogger(__name__)


def create_item(cog_hrefs: Dict[str, str]) -> Item:
    frequency = data_frequency(cog_hrefs["prcp"])
    basename = os.path.splitext(os.path.basename(cog_hrefs["prcp"]))[0]

    nominal_datetime: Optional[datetime] = None
    if frequency == Frequency.DAILY:
        id = basename[5:]
        year = int(id[0:4])
        month = int(id[4:6])
        day = int(id[-2:])
        start_datetime = datetime(year, month, day)
        end_datetime = datetime(year, month, day, 23, 59, 59)
        nominal_datetime = start_datetime
    else:
        id = f"nclimgrid-{basename[-6:]}"
        year = int(id[-6:-2])
        month = int(id[-2:])
        start_datetime = datetime(year, month, 1)
        end_datetime = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)
        nominal_datetime = None

    item = stactools.core.create.item(cog_hrefs["prcp"])
    item.id = id
    item.datetime = nominal_datetime
    item.common_metadata.start_datetime = start_datetime
    item.common_metadata.end_datetime = end_datetime
    item.common_metadata.created = datetime.now(tz=timezone.utc)

    item.assets.pop("data")
    for var in VARS:
        asset = asset_dict(frequency.value, var)
        asset["href"] = make_absolute_href(cog_hrefs[var])
        item.add_asset(var, Asset.from_dict(asset))

    item.stac_extensions.append(constants.RASTER_EXTENSION_V11)

    return item


def create_items(
    nc_href: str,
    cog_dir: str,
    existence_checker: Optional[Callable[[str], bool]] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> List[Item]:
    frequency = data_frequency(nc_href)
    nc_hrefs = nc_href_dict(nc_href)

    if read_href_modifier:
        read_nc_hrefs = {var: read_href_modifier(nc_hrefs[var]) for var in VARS}
    else:
        read_nc_hrefs = nc_hrefs

    items: List[Item] = []
    if frequency == Frequency.DAILY:
        days = day_indices(read_nc_hrefs["prcp"])
        for day in days:
            # TODO: existence checker here
            cog_paths = create_cogs(read_nc_hrefs, cog_dir, day=day)
            items.append(create_item(cog_paths))

    else:
        months = month_indices(read_nc_hrefs["prcp"])
        for month in months:
            # TODO: existence checker here
            cog_paths = create_cogs(read_nc_hrefs, cog_dir, month=month)
            items.append(create_item(cog_paths))

    return items


def create_collection(frequency: str) -> Collection:
    if frequency == Frequency.MONTHLY:
        collection = Collection(**constants.MONTHLY_COLLECTION)

        ScientificExtension.add_to(collection)
        collection.extra_fields["sci:doi"] = constants.MONTHLY_DATA_DOI
        collection.extra_fields["sci:citation"] = constants.MONTHLY_DATA_CITATION
        collection.extra_fields["sci:publications"] = constants.MONTHLY_DATA_PUBLICATION
        collection.add_link(constants.MONTHLY_DATA_LINK)

    else:
        collection = Collection(**constants.DAILY_COLLECTION)

    item_assets = {}
    for var in VARS:
        item_assets[var] = AssetDefinition(asset_dict(frequency, var))
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_ext.item_assets = item_assets

    collection.stac_extensions.append(constants.RASTER_EXTENSION_V11)

    collection.add_link(constants.LICENSE_LINK)

    return collection
