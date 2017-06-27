# This Python file uses the following encoding: utf-8
"""
atmcorr_timeseries.py, Sam Murphy (2017-06-26)

This module calculates surface surface reflectance through time for an Earth Engine
feature collection of cloud free radiances and atmospheric correction inputs.
Uses a 6S emulator (i.e. interpolated look up tables and elliptical orbit
correction)
"""

import math
# import mission_specifics (i.e. to handle satellite mission other than Sentinel 2)

def atmcorr(radiance, perihelion, day_of_year):
  """
  Atmospherically corrects radiance using correction coefficients
  at perihelion adjusted for Earth's ellipitcal orbit
  """
    
  # elliptical orbit correction
  elliptical_orbit_correction = 0.03275104*math.cos(math.radians(day_of_year/1.04137484)) + 0.96804905
  
  # correction coefficients
  a = perihelion[0] * elliptical_orbit_correction
  b = perihelion[1] * elliptical_orbit_correction

  # surface reflectance
  try:
    SR = (radiance - a) / b
  except:
    SR = None

  return SR


def surface_reflectance_timeseries(cloudFreeRadiance, iLUTs):
  """
  Atmospherically corrects mean, cloud-free pixel radiances
  returning a time series of surface reflectance values.
  """

  feature_collection = cloudFreeRadiance['features']
  
  # band names 
  # mission specific (Sentinel 2 hardcoded)
  #############################################################################
  ee_bandnames = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9','B10', 'B11', 'B12']
  py6s_bandnames = ['01','02','03','04','05','06','07','08','09','10','11','12','13']
  #############################################################################
  # TODO ee_bandnames = mission_specifics.ee_bandnames(mission)
  # TODO py6s_bandnames = mission_specifics.py6s_bandnames(mission)

  # surface reflectance output
  # (i.e. time series lists, stored in a dictionary)
  timeSeries = {'timeStamp':[]}
  for ee_bandname in ee_bandnames:
    timeSeries[ee_bandname] = []
  
  for feature in feature_collection:
    
    # time stamp
    timeSeries['timeStamp'].append(feature['properties']['timeStamp'])
    
    # mean average pixel radiances
    mean_averages = feature['properties']['mean_averages']

    # atmospheric correction inputs
    atmcorr_inputs = feature['properties']['atmcorr_inputs']
    solar_z = atmcorr_inputs['solar_z'] # solar zenith [degrees]
    h2o = atmcorr_inputs['h2o']         # water vapour column
    o3 = atmcorr_inputs['o3']           # ozone
    aot = atmcorr_inputs['aot']         # aerosol optical thickness
    alt = atmcorr_inputs['alt']         # altitude (above sea level, [km])
    day_of_year = atmcorr_inputs['doy'] # i.e. Jan 1st = 1

    # atmospheric correction (each waveband)
    for i, ee_bandname in enumerate(ee_bandnames):
      radiance = mean_averages[ee_bandname]
      iLUT = iLUTs.iLUTs[py6s_bandnames[i]]
      perihelion = iLUT(solar_z, h2o, o3, aot, alt)
      timeSeries[ee_bandname].append(atmcorr(radiance, perihelion, day_of_year))

  return timeSeries