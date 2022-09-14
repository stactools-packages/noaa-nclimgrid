import os
from calendar import monthrange
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import stactools.core.create
from pystac import Asset, Collection, Item
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.scientific import ScientificExtension
from pystac.utils import make_absolute_href
from stactools.core.io import ReadHrefModifier

from stactools.noaa_nclimgrid import constants
from stactools.noaa_nclimgrid.cog import create_cogs
from stactools.noaa_nclimgrid.constants import CollectionType, Frequency, Variable
from stactools.noaa_nclimgrid.utils import (
    cog_asset_dict,
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
    frequency = Frequency.from_href(cog_hrefs[Variable.PRCP])
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
        item.add_asset(var.value, Asset.from_dict(asset))
    if nc_hrefs:
        for var in Variable:
            asset = nc_asset_dict(frequency, var)
            asset["href"] = make_absolute_href(nc_hrefs[var])
            if nc_creation_dates:
                asset["created"] = nc_creation_dates[var]
            item.add_asset(f"{var.value}_source", Asset.from_dict(asset))

    item.stac_extensions.append(constants.RASTER_EXTENSION_V11)

    return item


def create_items(
    nc_href: str,
    cog_dir: str,
    nc_assets: bool = False,
    cog_check_href: Optional[str] = None,
    day_range: Optional[Tuple[int, int]] = None,
    month_range: Optional[Tuple[str, str]] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> Tuple[List[Item], List[str]]:
    """Creates STAC Items for temporal units in set of netCDF files.

    A temporal unit is a day for daily data or a month for monthly data. A set
    of netCDF files refers to 'prcp', 'tavg', 'tmin', and 'tmax'
    (:py:class:`Variable`) netCDF files for a common timespan, where the common
    timespan is 1895 to present for monthly data or a single month for daily
    data.

    Args:
        nc_href (str): HREF to a netCDF containing data for one of the four
            variables (prcp, tavg, tmax, tmin).
        cog_dir (str): Local destination directory for created COGs.
        nc_assets (bool): Flag to include Item assets for the source netCDF
            files. Default is False.
        cog_check_href (Optional[str]): HREF to a location to check for existing
            COG files. New COGs are not created if existing COGs are found. The
            `cog_check_href` can simply be the same local directory as
            `cog_href` or a remote directory, e.g., an Azure blob storage
            container.
        day_range (Optional[Tuple[int, int]]): An optional tuple of desired
            start and end day of month for daily data. For example:
            (<start_day_of_month>, <end_day_of_month>)
        month_range (Optional[Tuple[str, str]]): An optional tuple of desired
            start and end YYYYMM date strings. For example: (<start_YYYYMM>,
            <end_YYYYMM>).
        read_href_modifier (Optional[ReadHrefModifier]): An optional function
            to modify an href (e.g., to add a token to a url).

    Returns:
        Tuple[List[Item], List[str]]:
            1. A list of created STAC Items.
            2. A list of HREFs to any newly created COGs.
    """
    frequency = Frequency.from_href(nc_href)
    nc_hrefs = nc_href_dict(nc_href)

    if nc_assets:
        nc_creation_dates = nc_creation_date_dict(
            nc_hrefs, read_href_modifier=read_href_modifier
        )

    items: List[Item] = []
    created_cogs: List[str] = []
    if frequency == Frequency.DAILY:
        days = day_indices(
            nc_hrefs[Variable.PRCP],
            day_range=day_range,
            read_href_modifier=read_href_modifier,
        )
        for day in days:
            cog_hrefs, created_cog_hrefs = create_cogs(
                nc_hrefs,
                cog_dir,
                day=day,
                cog_check_href=cog_check_href,
                read_href_modifier=read_href_modifier,
            )
            created_cogs.extend(created_cog_hrefs)

            if nc_assets:
                items.append(create_item(cog_hrefs, nc_hrefs, nc_creation_dates))
            else:
                items.append(create_item(cog_hrefs))

    else:
        months = month_indices(
            nc_hrefs[Variable.PRCP],
            month_range=month_range,
            read_href_modifier=read_href_modifier,
        )
        for month in months:
            cog_hrefs, created_cog_hrefs = create_cogs(
                nc_hrefs,
                cog_dir,
                month=month,
                cog_check_href=cog_check_href,
                read_href_modifier=read_href_modifier,
            )
            created_cogs.extend(created_cog_hrefs)

            if nc_assets:
                items.append(create_item(cog_hrefs, nc_hrefs, nc_creation_dates))
            else:
                items.append(create_item(cog_hrefs))

    return (items, created_cogs)


def create_collection(
    collection_type: CollectionType, nc_assets: bool = False
) -> Collection:
    """Creates a STAC Collection for monthly or daily NClimGrid data.

    Args:
        collection_type (CollectionType): One of 'monthly', 'daily-prelim', or
            'daily-scaled'.
        nc_assets (bool): Flag to include Item assets for the source netCDF
            files. Default is False.

    Returns:
        Collection: A STAC collection for monthly or daily NClimGrid data.
    """
    if collection_type == CollectionType.MONTHLY:
        collection = Collection(**constants.MONTHLY_COLLECTION)
        ScientificExtension.add_to(collection)
        collection.extra_fields["sci:doi"] = constants.MONTHLY_DATA_DOI
        collection.extra_fields["sci:citation"] = constants.MONTHLY_DATA_CITATION
        collection.extra_fields["sci:publications"] = constants.MONTHLY_DATA_PUBLICATION
        collection.add_link(constants.MONTHLY_DATA_LINK)
    else:
        if collection_type == CollectionType.DAILY_PRELIM:
            collection = Collection(**constants.DAILY_PRELIM_COLLECTION)
        else:
            collection = Collection(**constants.DAILY_SCALED_COLLECTION)
        collection.add_link(constants.DAILY_DESCRIBEDBY_LINK)

    collection.providers = constants.PROVIDERS

    item_assets = {}
    frequency = (
        Frequency.MONTHLY
        if collection_type == CollectionType.MONTHLY
        else Frequency.DAILY
    )
    for var in Variable:
        item_assets[var.value] = AssetDefinition(cog_asset_dict(frequency, var))
    if nc_assets:
        for var in Variable:
            item_assets[f"{var.value}_source"] = AssetDefinition(
                nc_asset_dict(frequency, var)
            )
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_ext.item_assets = item_assets

    collection.stac_extensions.append(constants.RASTER_EXTENSION_V11)

    collection.add_links([constants.LICENSE_LINK, constants.LANDING_PAGE_LINK])

    return collection
