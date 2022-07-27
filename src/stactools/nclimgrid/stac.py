import logging
import os
from calendar import monthrange
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import stactools.core.create
from pystac import Asset, Item, MediaType
from pystac.utils import make_absolute_href
from stactools.core.io import ReadHrefModifier

from stactools.nclimgrid.cog import create_cogs
from stactools.nclimgrid.constants import (
    ASSET_TITLES,
    RASTER_BANDS,
    RASTER_EXTENSION_V11,
    VARS,
)
from stactools.nclimgrid.utils import (
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
    if frequency == "Daily":
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
        item.add_asset(
            var,
            Asset(
                href=make_absolute_href(cog_hrefs[var]),
                media_type=MediaType.COG,
                roles=["data"],
                title=f"{frequency} {ASSET_TITLES[var]}",
                extra_fields={"raster:bands": RASTER_BANDS[var]},
            ),
        )
    item.stac_extensions.append(RASTER_EXTENSION_V11)

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
    if frequency == "Daily":
        days = day_indices(read_nc_hrefs["prcp"])
        for day in days:
            if existence_checker:
                item_id = "todo"
                if existence_checker(item_id):
                    return items
            cog_paths = create_cogs(read_nc_hrefs, cog_dir, day=day)
            items.append(create_item(cog_paths))

    else:
        months = month_indices(read_nc_hrefs["prcp"])
        for month in months:
            if existence_checker:
                item_id = "todo"
                if existence_checker(item_id):
                    return items
            cog_paths = create_cogs(read_nc_hrefs, cog_dir, month=month)
            items.append(create_item(cog_paths))

    return items
