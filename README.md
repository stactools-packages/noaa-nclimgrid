# stactools-noaa-nclimgrid

[![PyPI](https://img.shields.io/pypi/v/stactools-noaa-nclimgrid)](https://pypi.org/project/stactools-noaa-nclimgrid/)

- Name: noaa-nclimgrid
- Package: `stactools.noaa-nclimgrid`
- PyPI: https://pypi.org/project/stactools-noaa-nclimgrid/
- Owner: @pjhartzell
- [Dataset homepage](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00332)
- STAC extensions used:
  - [item-assets](https://github.com/stac-extensions/item-assets)
  - [proj](https://github.com/stac-extensions/projection/)
  - [raster](https://github.com/stac-extensions/raster)
  - [scientific](https://github.com/stac-extensions/scientific)
- Extra fields:
  - `nclimgrid:daily_type`: One of `scaled` or `prelim` to indicate the type of daily data.

A stactools package for [NOAA NClimGrid](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00332) monthly and daily data covering the Continental United States (CONUS). The data consists of four variables:
- Precipitation (prcp) in millimeters
- Average temperature (tavg) in degree Celsius
- Minimum temperature (tmin) in degree Celsius
- Maximum temperature (tmax) in degree Celsius

The source monthly data is aggregated into four netCDF files, one for each variable, and dates back to 1895. Each monthly netCDF file is updated in place when data for a new month is available. 

The source daily data is aggregated into monthly netCDF files, with one file for each of the four variables, and dates back to 1951. Daily data files are marked as either "prelim" or "scaled". The most recent data, i.e., the current month, is preliminary ("prelim") and the NetCDF files are updated in place as data for a new day is made available. Once the month is completed, the preliminary data is scaled to match the corresponding monthly values and a new "scaled" NetCDF file is made available.

## STAC Examples

- Monthly
  - [Example Collection and Items in JSON form](examples/monthly)
  - [Browse the example STAC](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/noaa-nclimgrid/main/examples/monthly/collection.json)
- Daily - Preliminary
  - [Example Collection and Items in JSON form](examples/daily-prelim)
  - [Browse the example STAC](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/noaa-nclimgrid/main/examples/daily-prelim/collection.json)
- Daily - Scaled
  - [Example Collection and Items in JSON form](examples/daily-scaled)
  - [Browse the example STAC](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/noaa-nclimgrid/main/examples/daily-scaled/collection.json)

## Installation

```shell
pip install stactools-noaa-nclimgrid
```

## Command-line Usage

### Items

When using the command-line interface, COGs and Items are created for all months (monthly data) or all days in a month (daily data). Although four netCDF files are required to create a single Item (each netCDF contains data for one of the four variables), only a single HREF to one of the four netCDF files is required to create Items. The remaining three netCDFs are assumed to exist in the same directory as the specified HREF.

```shell
stac noaa-nclimgrid create-items <href to one netCDF file> <cog output directory> <item output directory>
```

### Collections

A monthly or daily collection and corresponding COGs and Items can be created by adding netCDF HREFs to a text file. The COGs will be stored alongside the Items.

```shell
stac noaa-nclimgrid create-collection <text file path> <output directory>
```

For example, the monthly Collection, Items, and COGs found in the `examples/monthly` directory can be created with:
```shell
stac noaa-nclimgrid create-collection --nc-assets examples/file-list-monthly.txt examples
```

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
pip install -e .
pip install -r requirements-dev.txt
pre-commit install
```

To check all files:

```shell
pre-commit run --all-files
```

To run the tests:

```shell
pytest -vv
```
