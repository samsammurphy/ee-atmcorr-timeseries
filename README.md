## Introduction

Atmospherically corrected time series of satellite imagery from Google Earth Engine using the [6S emulator](https://github.com/samsammurphy/6S_emulator/edit/master/README.md).

## Installation

Install [Docker](https://docs.docker.com/engine/installation/#supported-platforms).

If this command works, you have successfully installed Docker.

`docker run hello-world`

## Usage

1) run the docker container that contains all the dependencies

`docker run -i -t -p 8888:8888 samsammurphy/ee-python3-jupyter-atmcorr-timeseries:v1.5`

(this will download everything you need).

2) authenticate the Earth Engine API.

`earthengine authenticate`

(this will print out a URL "Opening web browser to address: https://..." which needs to be opened in a web browser)

3) pull in any updates

`cd ee-atmcorr-timeseries`
`git pull`

4) run the jupyter notebook

`jupyter-notebook jupyter_notebooks/ee-atmcorr-timeseries.ipynb --ip='*' --port=8888 --allow-root`

(open the URL: http:/localhost..)
