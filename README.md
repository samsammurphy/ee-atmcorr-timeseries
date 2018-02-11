## Atmospheric Correction of Sentinel2 and Landsat

Consider using [gee-atmcorr-S2](https://github.com/samsammurphy/gee-atmcorr-S2) if you are atmospherically correcting a small number of images (e.g. 10s). It uses [Py6S](http://py6s.readthedocs.io/en/latest/) directly and has less set up time. 

## Purpose

This repo is for atmospherically correcting large numbers (e.g. 100s) of Sentinel2 and Landsat images. Although automated, it has a longer set up time as it will download then interpolate look up tables. However, it should run considerably faster. Time series have the following properties:

* atmospherically corrected
* cloud-masked
* saved to excel
* pretty plots

## Installation

Install [Docker](https://docs.docker.com/install/) then build the Dockerfile

`docker build /path/to/Dockerfile -t atmcorr-timeseries`

## Usage

Run the Docker container.

`docker run -i -t -p 8888:8888 atmcorr-timeseries`

and authenticate the Earth Engine API.

`earthengine authenticate`

 grab the source code

`git clone https://github.com/samsammurphy/ee-atmcorr-timeseries`

and run the Jupyter Notebook:

```
cd ee-atmcorr-timeseries/jupyter_notebooks
jupyter-notebook ee-atmcorr-timeseries.ipynb --ip='*' --port=8888 --allow-root
```

## Notes on setup-time VS run-time

This code is optimized to run atmospheric correction of large image collections. It trades setup-time (i.e. ~30 mins) for run time. Setup is only performed once and is fully automated. This solves the problem of running radiative transfer code for each image which would take ~2 secs/scene, 500 scenes would therefore take over 16 mins (everytime).

It does this using the [6S emulator](https://github.com/samsammurphy/6S_emulator) which is based on n-dimensional interpolated lookup tables (iLUTs). These iLUTs are automatically downloaded and constructed locally.
