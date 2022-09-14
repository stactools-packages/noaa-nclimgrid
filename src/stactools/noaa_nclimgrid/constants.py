import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

from pystac import Extent, Link, Provider, ProviderRole, SpatialExtent, TemporalExtent


class Frequency(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"

    @staticmethod
    def from_href(href: str) -> "Frequency":
        basename = os.path.splitext(os.path.basename(href))[0]
        return (
            Frequency.MONTHLY if basename.startswith("nclimgrid") else Frequency.DAILY
        )


class CollectionType(str, Enum):
    MONTHLY = "monthly"
    DAILY_PRELIM = "daily-prelim"
    DAILY_SCALED = "daily-scaled"

    @staticmethod
    def from_href(href: str) -> "CollectionType":
        basename = os.path.splitext(os.path.basename(href))[0]
        if basename.startswith("nclimgrid"):
            return CollectionType.MONTHLY
        elif "prelim" in basename:
            return CollectionType.DAILY_PRELIM
        else:
            return CollectionType.DAILY_SCALED


class Variable(str, Enum):
    PRCP = "prcp"
    TAVG = "tavg"
    TMAX = "tmax"
    TMIN = "tmin"


COG_ASSET_TITLES = {
    Variable.PRCP: "Precipitation (mm)",
    Variable.TAVG: "Average Temperature (degree Celsius)",
    Variable.TMAX: "Maximmum Temperature (degree Celsius)",
    Variable.TMIN: "Minimum Temperature (degree Celsius)",
}
COG_ROLES = ["data"]
COG_RASTER_BANDS = {
    Variable.PRCP: [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "mm",
            "spatial_resolution": 5000,
        }
    ],
    Variable.TAVG: [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "degree Celsius",
            "spatial_resolution": 5000,
        }
    ],
    Variable.TMAX: [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "degree Celsius",
            "spatial_resolution": 5000,
        }
    ],
    Variable.TMIN: [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "degree Celsius",
            "spatial_resolution": 5000,
        }
    ],
}
RASTER_EXTENSION_V11 = "https://stac-extensions.github.io/raster/v1.1.0/schema.json"

NETCDF_MEDIA_TYPE = "application/netcdf"
NETCDF_ASSET_TITLES = {
    Variable.PRCP: "Precipitation Source Data",
    Variable.TAVG: "Average Temperature Source Data",
    Variable.TMAX: "Maximmum Temperature Source Data",
    Variable.TMIN: "Minimum Temperature Source Data",
}
NETCDF_ROLES = ["data", "source"]


LICENSE_LINK = Link(
    rel="license",
    target=(
        "https://www.ncei.noaa.gov/access/metadata/landing-page/bin/"
        "iso?id=gov.noaa.ncdc:C00332#Constraints"
    ),
    title="NClimGrid Data Use and Access Constraints",
    media_type="text/html",
)
LANDING_PAGE_LINK = Link(
    rel="about",
    media_type="text/html",
    title="Product Landing Page",
    target="https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00332",
)

PROVIDERS = [
    Provider(
        name="NOAA National Centers for Environmental Information",
        roles=[ProviderRole.PRODUCER, ProviderRole.LICENSOR],
        url="https://www.ncei.noaa.gov/",
    )
]

KEYWORDS = [
    "NOAA",
    "NClimGrid",
    "Air Temperature",
    "Precipitation",
    "Surface Observations",
    "Climatology",
    "CONUS",
]

MONTHLY_COLLECTION: Dict[str, Any] = {
    "id": "noaa-nclimgrid-monthly",
    "title": "Monthly NOAA U.S. Climate Gridded Dataset (NClimGrid)",
    "description": (
        "The Monthly NOAA U.S. Climate Gridded Dataset (NClimGrid) consists of "
        "four climate variables derived from the Global Historical Climatology "
        "Network Daily dataset (GHCN-D): maximum temperature, minimum temperature, "
        "average temperature, and precipitation. Monthly values in a 1/24 degree "
        "lat/lon grid (nominal 5x5 kilometer) are provided for the Continental "
        "United States. Monthly data is available from 1895 to the present."
    ),
    "license": "proprietary",
    "keywords": KEYWORDS,
    "extent": Extent(
        SpatialExtent([[-124.708333, 24.541666, -66.999995, 49.375001]]),
        TemporalExtent([[datetime(1895, 1, 1, tzinfo=timezone.utc), None]]),
    ),
}
MONTHLY_DATA_DOI = "10.7289/V5SX6B56"
MONTHLY_DATA_CITATION = (
    "Vose, Russell S., Applequist, Scott, Squires, Mike, Durre, Imke, Menne, "
    "Matthew J., Williams, Claude N. Jr., Fenimore, Chris, Gleason, Karin, and "
    "Arndt, Derek (2014): NOAA Monthly U.S. Climate Gridded Dataset (NClimGrid)"
    ", Version 1. NOAA National Centers for Environmental Information. "
    "DOI:10.7289/V5SX6B56."
)
MONTHLY_DATA_PUBLICATION = [
    {
        "doi": "10.1175/JAMC-D-13-0248.1",
        "citation": (
            "Vose, R. S., Applequist, S., Squires, M., Durre, I., Menne, M. J., "
            "Williams, C. N., Jr., Fenimore, C., Gleason, K., & Arndt, D. (2014). "
            "Improved Historical Temperature and Precipitation Time Series for U.S."
            " Climate Divisions, Journal of Applied Meteorology and Climatology, "
            "53(5), 1232-1251."
        ),
    }
]
MONTHLY_DATA_LINK = Link(
    rel="cite-as",
    target="https://doi.org/10.7289/V5SX6B56",
    title="NOAA Monthly U.S. Climate Gridded Dataset (NClimGrid)",
    media_type="text/html",
)

DAILY_EXTENT = Extent(
    SpatialExtent([[-124.708333, 24.541666, -66.999995, 49.375001]]),
    TemporalExtent([[datetime(1951, 1, 1, tzinfo=timezone.utc), None]]),
)
DAILY_LICENSE = "proprietary"
DAILY_SCALED_COLLECTION: Dict[str, Any] = {
    "id": "noaa-nclimgrid-daily-scaled",
    "title": "NOAA Daily U.S. Climate Gridded Dataset - Scaled",
    "description": (
        "The NOAA Daily U.S. Climate Gridded Dataset (NClimGrid-d) consists of "
        "four climate variables derived from the Global Historical Climatology "
        "Network Daily dataset (GHCN-D): maximum temperature, minimum temperature, "
        "average temperature, and precipitation. Daily values in a 1/24 degree "
        "lat/lon (nominal 5x5 kilometer) grid are provided for the Continental "
        "United States and are available from 1951 to the present. The data in "
        "this Collection are scaled to match the corresponding monthly "
        "values."
    ),
    "license": DAILY_LICENSE,
    "keywords": KEYWORDS,
    "extent": DAILY_EXTENT,
}
DAILY_PRELIM_COLLECTION: Dict[str, Any] = {
    "id": "noaa-nclimgrid-daily-prelim",
    "title": "NOAA Daily U.S. Climate Gridded Dataset - Preliminary",
    "description": (
        "The NOAA Daily U.S. Climate Gridded Dataset (NClimGrid-d) consists of "
        "four climate variables derived from the Global Historical Climatology "
        "Network Daily dataset (GHCN-D): maximum temperature, minimum temperature, "
        "average temperature, and precipitation. Daily values in a 1/24 degree "
        "lat/lon (nominal 5x5 kilometer) grid are provided for the Continental "
        "United States and are available from 1951 to the present. The data in "
        "this Collection are preliminary and are not scaled to match the "
        "corresponding monthly values."
    ),
    "license": DAILY_LICENSE,
    "keywords": KEYWORDS,
    "extent": DAILY_EXTENT,
}
DAILY_DESCRIBEDBY_LINK = Link(
    rel="describedby",
    target="https://www1.ncdc.noaa.gov/pub/data/daily-grids/docs/nclimdiv-description.pdf",
    title="NOAA Daily NClimGrid Product Description",
    media_type="application/pdf",
)
