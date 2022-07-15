# stactools-nclimgrid

[![PyPI](https://img.shields.io/pypi/v/stactools-nclimgrid)](https://pypi.org/project/stactools-nclimgrid/)

- Name: nclimgrid
- Package: `stactools.nclimgrid`
- PyPI: https://pypi.org/project/stactools-nclimgrid/
- Owner: @githubusername
- Dataset homepage: http://example.com
- STAC extensions used:
  - [proj](https://github.com/stac-extensions/projection/)
  - [raster](https://github.com/stac-extensions/raster)

A stactools package for [NClimGrid](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00332) data. In development.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
$ pip install -e .
$ pip install -r requirements-dev.txt
$ pre-commit install
```

To check all files:

```shell
$ pre-commit run --all-files
```

To run the tests:

```shell
$ pytest -vv
```
