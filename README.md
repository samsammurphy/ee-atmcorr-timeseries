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

