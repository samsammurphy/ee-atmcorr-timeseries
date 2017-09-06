"""
ee_requests.py, Sam Murphy (2017-06-22)

Set's up batch requests for reduced data from Earth Engine.

Returns a feature collection which could be input into, for exampled:

 - export (e.g to csv)
 - getInfo (e.g. for usage in a notebook with less end-user hoops to jump through)

..depending on workflow
"""

import ee
from atmospheric import Atmospheric
from cloudRemover import CloudRemover
import mission_specifics

class AtmcorrInput:
  """
  Grabs the inputs required for atmospheric correction
  """

  # global elevation (kilometers)
  elevation = ee.Image('USGS/GMTED2010').divide(1000)

  def get():
    
    altitude = AtmcorrInput.elevation.reduceRegion(\
        reducer = ee.Reducer.mean(),\
        geometry = TimeSeries.geom.centroid()\
        )

    return ee.Dictionary({
      'solar_z':mission_specifics.solar_z(TimeSeries.image, TimeSeries.mission),
      'h2o':Atmospheric.water(TimeSeries.geom,TimeSeries.date),
      'o3':Atmospheric.ozone(TimeSeries.geom,TimeSeries.date),
      'aot':Atmospheric.aerosol(TimeSeries.geom,TimeSeries.date),
      'alt':altitude.get('be75'),
      'doy':TimeSeries.day_of_year
      })
  
class TimeSeries:
  """
  This class is used to extract (cloud-free) mean-average radiance values 
  contained within an earth engine geometry for all images in a collection,
  It also gathers the atmospheric correction input variables required to 
  get surface reflectance from at-sensor radiance.
  """

  def meanReduce(image, geom):
    """
    Calculates mean average pixel values in a geometry
    """    
    
    mean_averages = image.reduceRegion(\
          reducer = ee.Reducer.mean(),\
          geometry = geom)
    
    return mean_averages
   
  def radianceFromTOA():
    """
    calculate at-sensor radiance from top-of-atmosphere (TOA) reflectance
    """

    toa = mission_specifics.TOA(TimeSeries.image, TimeSeries.mission)

    ESUNs = mission_specifics.ESUNs(TimeSeries.image, TimeSeries.mission)

    wavebands = mission_specifics.ee_bandnames(TimeSeries.mission)

    # solar zenith (radians)
    theta = mission_specifics.solar_z(TimeSeries.image, TimeSeries.mission).multiply(0.017453293)

    pi = ee.Number(3.14159265359)

    # Earth-Sun distance squared (AU)
    d = ee.Number(TimeSeries.day_of_year).subtract(4).multiply(0.017202).cos().multiply(-0.01672).add(1)
    d_squared = d.multiply(d)

    radiance = toa.select(ee.List(wavebands)).multiply(ESUNs).multiply(theta.cos()).divide(pi).divide(d_squared)

    return radiance
  
  def meanBT():
    
    tir_waveband = mission_specifics.tir_bandnames(TimeSeries.mission)
    
    brightness_temperature = TimeSeries.image.select(tir_waveband)

    mean_brightness_temperature = TimeSeries.meanReduce(brightness_temperature, TimeSeries.geom)

    return mean_brightness_temperature

  def extractor(image):
    
    # update TimeSeries class
    TimeSeries.image = image
    TimeSeries.date = ee.Date(image.get('system:time_start'))
    jan01 = ee.Date.fromYMD(TimeSeries.date.get('year'),1,1)
    TimeSeries.day_of_year = ee.Number(TimeSeries.date.difference(jan01,'day')).add(1)
    
    cloudRemover = TimeSeries.cloudRemover.fromMission(TimeSeries.mission)
    TimeSeries.image = cloudRemover(image)

    radiance = TimeSeries.radianceFromTOA()

    mean_radiance = TimeSeries.meanReduce(radiance, TimeSeries.geom)

    atmcorr_inputs = AtmcorrInput.get()

    isSentinel2 = ee.String(TimeSeries.mission).match('Sentinel2')
    brightness_temperature = ee.Algorithms.If(isSentinel2, {'na':None}, TimeSeries.meanBT())

    properties = {
      'mission':TimeSeries.mission,
      'imageID':image.get('system:index'),
      'timeStamp':ee.Number(image.get('system:time_start')).divide(1000),
      'mean_radiance':mean_radiance,
      'atmcorr_inputs':atmcorr_inputs,
      'brightness_temperature': brightness_temperature
    } 

    return ee.Feature(TimeSeries.geom, properties)

def data_request(geom, startDate, stopDate, mission):
  """
  Creates Earth Engine invocation for data:
    - mean radiance 
    - atmospheric correction inputs (VSWIR bands)
    - brightness temperature (if available)
    
  from within a geometry through time after cloud mask
  """

  TimeSeries.geom = geom
  TimeSeries.startDate = ee.Date(startDate)
  TimeSeries.stopDate = ee.Date(stopDate)

  TimeSeries.mission = mission
  
  TimeSeries.cloudRemover = CloudRemover  

  ic = ee.ImageCollection(mission_specifics.eeCollection(mission))\
    .filterBounds(geom)\
    .filterDate(startDate, stopDate)\
    .filter(mission_specifics.sunAngleFilter(mission))

  data = ic.map(TimeSeries.extractor).sort('timestamp')

  return ee.FeatureCollection(data)