## Purpose

Easily create time series of Landsat and Sentinel 2 data for anywhere on Earth. 

* atmospherically corrected
* cloud-masked
* save to excel
* pretty plots

## Installation

Install [Anaconda](https://www.continuum.io/downloads).

If necessary, create a python3 environment

`conda create --name py3 python=3`

and activate it

`source activate py3`

on windows the above command is just

`activate py3`

then install the Earth Engine API

```
pip install google-api-python-client
pip install earthengine-api 
```

## Usage

If first time, authenticate the Earth Engine API.

`earthengine authenticate`

 grab source code

`git clone https://github.com/samsammurphy/ee-atmcorr-timeseries`

run in Jupyter Notebook:

```
cd ee-atmcorr-timeseries/jupyter_notebooks
jupyter-notebook ee-atmcorr-timeseries.ipynb
```

## Setup-time VS Run-time

This code is optimized to run atmospheric correction of large image collections. It trades setup-time (i.e. ~30 mins) for run time (i.e. ~ 1 minute). Setup is only performed once and is fully automated. This solves the problem of running radiative transfer code for each image which would take ~2 secs/scene, 500 scenes would therefore take over 16 mins (everytime).

It does this using the [6S emulator](https://github.com/samsammurphy/6S_emulator) which is based on n-dimensional interpolated lookup tables (iLUTs). These iLUTs are automatically downloaded and constructed locally.
