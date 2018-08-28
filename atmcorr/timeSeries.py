import os
import ee
import pandas as pd

import atmcorr.interpolated_lookup_tables as iLUT
from atmcorr.ee_requests import request_meanRadiance
from atmcorr.atmcorr_timeseries import surface_reflectance_timeseries
from atmcorr.mission_specifics import ee_bandnames, common_bandnames

def timeseries_extrator(geom, startDate, stopDate, mission, removeClouds=True):
    """
    This is the function for extracting atmospherically corrected, 
    cloud-free time series for a given satellite mission.
    """
    
    # interpolated lookup tables 
    iLUTs = iLUT.handler(mission) 
    iLUTs.get()
    
    # earth engine request
    print('Getting data from Earth Engine.. ')
    request = request_meanRadiance(geom, ee.Date(startDate), ee.Date(stopDate), \
                                   mission, removeClouds)
    meanRadiance = request.getInfo()
    print('Data collection complete')
    
    # return if no pixels available
    num = len(meanRadiance['features'])
    if num == 0:
        return {}
    else:
        print('number of valid images = {}'.format(num))
    
    # atmospheric correction
    print('Running atmospheric correction')
    timeseries = surface_reflectance_timeseries(meanRadiance, iLUTs, mission)
    print('Done')
    
    return timeseries  

def extractAllTimeSeries(target, geom, startDate, stopDate, missions, removeClouds=True):
    """
    Extracts time series for each mission and join them together
    """ 
    
    # will store results here (and use consistent band names)
    allTimeSeries = {
        'blue':[], 
        'green':[], 
        'red':[], 
        'nir':[],
        'swir1':[], 
        'swir2':[],
        'timeStamp':[]
    }

    # for mission in ['Landsat4']:
    for mission in missions:
        
        timeseries = timeseries_extrator(geom, startDate, stopDate, mission, removeClouds=removeClouds) 
        
        # names of wavebands
        eeNames = ee_bandnames(mission)
        commonNames = common_bandnames(mission)
        
        # add mission to timeseries
        for key in timeseries.keys():
            if key[0] == 'B':
                commonName = commonNames[eeNames.index(key)]
                if commonName in allTimeSeries.keys():
                    allTimeSeries[commonName].append(timeseries[key])
            if key == 'timeStamp':
                allTimeSeries['timeStamp'].append(timeseries['timeStamp'])
    
    # flatten each variables (from separate missions) into a single list
    def flatten(multilist):
        if isinstance(multilist[0], list):
            return [item for sublist in multilist for item in sublist]
        else:
            return multilist

    for key in allTimeSeries.keys():
        allTimeSeries[key] = flatten(allTimeSeries[key])
    
    return allTimeSeries

def saveToExcel(target, allTimeSeries):
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_dir = os.path.join(basedir,'files','excel')
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)
    
    # create pandas data frame
    df = pd.DataFrame.from_dict(allTimeSeries)

    # save to excel
    df.to_excel(os.path.join(excel_dir, target+'.xlsx'), index=False)

def loadFromExcel(target):
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(basedir,'files','excel',target+'.xlsx')

    if os.path.isfile(excel_path):
      print('Loading from excel file')
      return pd.read_excel(excel_path).to_dict(orient='list')

def timeSeries(target, geom, startDate, stopDate, missions, removeClouds=True):
    """
    time series flow
    1) try loading from excel
    2) run the extraction
    3) save to excel
    """

    # try loading from excel first
    try:
      allTimeSeries = loadFromExcel(target)
      if allTimeSeries:
        return allTimeSeries
    except:
      pass
       
    # run extraction
    allTimeSeries = extractAllTimeSeries(target, geom, startDate, stopDate, missions)

    # save to excel
    saveToExcel(target, allTimeSeries)

    return allTimeSeries