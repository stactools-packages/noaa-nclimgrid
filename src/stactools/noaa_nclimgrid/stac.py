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

from stactools.noaa_nclimgrid import constants
from stactools.noaa_nclimgrid.cog import create_cogs
from stactools.noaa_nclimgrid.constants import Frequency, Variable
from stactools.noaa_nclimgrid.utils import (
    cog_asset_dict,
    data_frequency,
    day_indices,
    month_indices,
    nc_asset_dict,
    nc_creation_date_dict,
    nc_href_dict,
)


def create_item(
    cog_hrefs: Dict[Variable, str],
    nc_hrefs: Optional[Dict[Variable, str]] = None,
    nc_creation_dates: Optional[Dict[Variable, str]] = None,
) -> Item:
    """Creates a STAC Item with COG assets for a single temporal unit.

    A temporal unit is a day for daily data or a month for monthly data.

    Args:
        cog_hrefs (Dict[Variable, str]): A dictionary mapping variables (keys) to
            COG HREFs (values).
        nc_hrefs (Optional[Dict[Variable, str]]): An optional dictionary mapping
            variables (keys) to netCDF HREFs (values). If present, assets for
            the source netCDF files will be included in the created Item.
        nc_creation_dates (Optional[Dict[Variable, datetime]): An optional
            dictionary mapping variables to netCDF file creation dates.

    Returns:
        Item: A STAC Item.
    """
    frequency = data_frequency(cog_hrefs[Variable.PRCP])
    basename = os.path.splitext(os.path.basename(cog_hrefs[Variable.PRCP]))[0]

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

    item = stactools.core.create.item(cog_hrefs[Variable.PRCP])
    item.id = id
    item.datetime = nominal_datetime
    item.common_metadata.start_datetime = start_datetime
    item.common_metadata.end_datetime = end_datetime
    item.common_metadata.created = datetime.now(tz=timezone.utc)

    item.assets.pop("data")
    for var in Variable:
        asset = cog_asset_dict(frequency, var)
        asset["href"] = make_absolute_href(cog_hrefs[var])
        item.add_asset(var, Asset.from_dict(asset))
    if nc_hrefs:
        for var in Variable:
            asset = nc_asset_dict(frequency, var)
            asset["href"] = make_absolute_href(nc_hrefs[var])
            if nc_creation_dates:
                asset["creation"] = nc_creation_dates[var]
            item.add_asset(f"{var}_source", Asset.from_dict(asset))

    item.stac_extensions.append(constants.RASTER_EXTENSION_V11)

    return item


def create_items(
    nc_href: str,
    cog_dir: str,
    nc_assets: bool = False,
    short_circuit: Optional[Callable[[str], bool]] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> List[Item]:
    """Creates STAC Items for all temporal units in set of netCDF files.

    A temporal unit is a day for daily data or a month for monthly data. A set
    of netCDF files refers to 'prcp', 'tavg', 'tmin', and 'tmax'
    (:py:class:`Variable`) netCDF files for a common timespan, where the common
    timespan is 1895 to present for monthly data or a single month for daily
    data.

    Args:
        nc_href (str): HREF to a netCDF containing data for one of the four
            variables (prcp, tavg, tmax, tmin).
        cog_dir (str): Destination directory for COGs which will be created.
        nc_assets (bool): Flag to include Item assets for the source netCDF
            files. Default is False.
        short_circuit (Optional[Callable[[str], bool]]): A placeholder
            for an optional function that checks for existing Items and/or COGs.
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        List[Item]: A list of the created STAC Items.
    """
    frequency = data_frequency(nc_href)
    nc_hrefs = nc_href_dict(nc_href)

    if read_href_modifier:
        read_nc_hrefs = {
            var: read_href_modifier(nc_hrefs[var]) for var in nc_hrefs.keys()
        }
    else:
        read_nc_hrefs = nc_hrefs

    if nc_assets:
        nc_creation_dates = nc_creation_date_dict(read_nc_hrefs)

    items: List[Item] = []
    if frequency == Frequency.DAILY:
        days = day_indices(read_nc_hrefs[Variable.PRCP])
        for day in days:
            # TODO: short_circuit here
            cog_paths = create_cogs(read_nc_hrefs, cog_dir, day=day)
            if nc_assets:
                items.append(create_item(cog_paths, nc_hrefs, nc_creation_dates))
            else:
                items.append(create_item(cog_paths))

    else:
        months = month_indices(read_nc_hrefs[Variable.PRCP])
        for month in months:
            # TODO: short_circuit here
            cog_paths = create_cogs(read_nc_hrefs, cog_dir, month=month)
            if nc_assets:
                items.append(create_item(cog_paths, nc_hrefs, nc_creation_dates))
            else:
                items.append(create_item(cog_paths))

    return items


def create_collection(frequency: Frequency, nc_assets: bool = False) -> Collection:
    """Creates a STAC Collection for monthly or daily NClimGrid data.

    Args:
        frequency (Frequency): One of 'monthly' or 'daily'.
        nc_assets (bool): Flag to include Item assets for the source netCDF
            files. Default is False.

    Returns:
        Collection: A STAC collection for monthly or daily NClimGrid data.
    """
    if frequency == Frequency.MONTHLY:
        collection = Collection(**constants.MONTHLY_COLLECTION)

        ScientificExtension.add_to(collection)
        collection.extra_fields["sci:doi"] = constants.MONTHLY_DATA_DOI
        collection.extra_fields["sci:citation"] = constants.MONTHLY_DATA_CITATION
        collection.extra_fields["sci:publications"] = constants.MONTHLY_DATA_PUBLICATION
        collection.add_link(constants.MONTHLY_DATA_LINK)

    else:
        collection = Collection(**constants.DAILY_COLLECTION)
        collection.add_link(constants.DAILY_DESCRIBEDBY_LINK)

    collection.providers = constants.PROVIDERS

    item_assets = {}
    for var in Variable:
        item_assets[var.value] = AssetDefinition(cog_asset_dict(frequency, var))
    if nc_assets:
        for var in Variable:
            item_assets[f"{var}_source"] = AssetDefinition(
                nc_asset_dict(frequency, var)
            )
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_ext.item_assets = item_assets

    collection.stac_extensions.append(constants.RASTER_EXTENSION_V11)

    collection.add_links([constants.LICENSE_LINK, constants.LANDING_PAGE_LINK])

    return collection
