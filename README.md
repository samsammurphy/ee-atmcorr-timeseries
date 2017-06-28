## Introduction

Atmospherically corrected time series of satellite imagery from Google Earth Engine using the [6S emulator](https://github.com/samsammurphy/6S_emulator/edit/master/README.md).

## Installation

Install [Anaconda](https://www.continuum.io/downloads).

If necessary, create a python3 environment

`conda create -n my_python3_env`

To use this environment, activate it as follows:

`source activate my_python3_env`

.. if on Windows the command is a bit shorter:

`activate my_python3_env`

If necessary, install the Earth Engine API:

```
pip install google-api-python-client
pip install earthengine-api 
```

## Usage

Authenticate the Earth Engine API.

`earthengine authenticate`

see the Jupyter Notebook for example usage

