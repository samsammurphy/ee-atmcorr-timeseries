def timeseries_extrator(mission):
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

def get_allTimeSeries(missions):
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
        
        timeseries = timeseries_extrator(mission) 
        
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
    
    # flatten each mission into a single list
    def flatten(multilist):
        if isinstance(multilist[0], list):
            return [item for sublist in multilist for item in sublist]
        else:
            return multilist

    for key in allTimeSeries.keys():
        allTimeSeries[key] = flatten(allTimeSeries[key])

    return allTimeSeries