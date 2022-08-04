from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

from pystac import Extent, Link, Provider, ProviderRole, SpatialExtent, TemporalExtent


class Frequency(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"


class Variable(str, Enum):
    PRCP = "prcp"
    TAVG = "tavg"
    TMAX = "tmax"
    TMIN = "tmin"


ASSET_TITLES = {
    Variable.PRCP: "Precipitation (mm)",
    Variable.TAVG: "Average Temperature (degree Celsius)",
    Variable.TMAX: "Maximmum Temperature (degree Celsius)",
    Variable.TMIN: "Minimum Temperature (degree Celsius)",
}

RASTER_BANDS = {
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
    "id": "nclimgrid-monthly",
    "title": "NOAA Monthly U.S. Climate Gridded Dataset (NClimGrid)",
    "description": (
        "The NOAA Monthly U.S. Climate Gridded Dataset (NClimGrid) consists of "
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

DAILY_COLLECTION: Dict[str, Any] = {
    "id": "nclimgrid-daily",
    "title": "NOAA Daily U.S. Climate Gridded Dataset (NClimGrid-d)",
    "description": (
        "The NOAA Daily U.S. Climate Gridded Dataset (NClimGrid-d) consists of "
        "four climate variables derived from the Global Historical Climatology "
        "Network Daily dataset (GHCN-D): maximum temperature, minimum temperature, "
        "average temperature, and precipitation. Daily values in a 1/24 degree "
        "lat/lon (nominal 5x5 kilometer) grid are provided for the Continental "
        "United States. Daily data is available from 1951 to the present."
    ),
    "license": "proprietary",
    "keywords": KEYWORDS,
    "extent": Extent(
        SpatialExtent([[-124.708333, 24.541666, -66.999995, 49.375001]]),
        TemporalExtent([[datetime(1951, 1, 1, tzinfo=timezone.utc), None]]),
    ),
}
DAILY_DESCRIBEDBY_LINK = Link(
    rel="describedby",
    target="https://www1.ncdc.noaa.gov/pub/data/daily-grids/docs/nclimdiv-description.pdf",
    title="NOAA Daily NClimGrid Product Description",
    media_type="application/pdf",
)
