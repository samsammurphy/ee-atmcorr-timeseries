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
          geometry = geom,\
          maxPixels = 2E7)
    
    return mean_averages
   
  def radianceFromTOA():
    """
    calculate at-sensor radiance from top-of-atmosphere (TOA) reflectance
    """

    # top of atmosphere reflectance
    toa = mission_specifics.TOA(TimeSeries.image, TimeSeries.mission)

    # solar irradiances
    ESUNs = mission_specifics.ESUNs(TimeSeries.image, TimeSeries.mission)

    # wavebands
    bands = mission_specifics.ee_bandnames(TimeSeries.mission)

    # solar zenith (radians)
    theta = mission_specifics.solar_z(TimeSeries.image, TimeSeries.mission).multiply(0.017453293)

    # circular math
    pi = ee.Number(3.14159265359)

    # Earth-Sun distance squared (AU)
    d = ee.Number(TimeSeries.day_of_year).subtract(4).multiply(0.017202).cos().multiply(-0.01672).add(1)
    d_squared = d.multiply(d)

    # radiance at-sensor
    rad = toa.select(ee.List(bands)).multiply(ESUNs).multiply(theta.cos()).divide(pi).divide(d_squared)

    return rad
  
  def extractor(image):
    
    # update TimeSeries class
    TimeSeries.image = image
    TimeSeries.date = ee.Date(image.get('system:time_start'))
    jan01 = ee.Date.fromYMD(TimeSeries.date.get('year'),1,1)
    TimeSeries.day_of_year = ee.Number(TimeSeries.date.difference(jan01,'day')).add(1)
    
    # remove clouds and shadows?
    if TimeSeries.removeClouds:
      cloudRemover = TimeSeries.cloudRemover.fromMission(TimeSeries.mission)
      TimeSeries.image = cloudRemover(image)

    # radiance at-sensor
    radiance = TimeSeries.radianceFromTOA()

    # mean average radiance
    mean_averages = TimeSeries.meanReduce(radiance, TimeSeries.geom)

    # atmospheric correction inputs
    atmcorr_inputs = AtmcorrInput.get()
    
    # export to feature collection
    properties = {
      'mission':TimeSeries.mission,
      'imageID':image.get('system:index'),
      'timeStamp':ee.Number(image.get('system:time_start')).divide(1000),
      'mean_averages':mean_averages,
      'atmcorr_inputs':atmcorr_inputs      
    }  

    return ee.Feature(TimeSeries.geom, properties)

def request_meanRadiance(geom, startDate, stopDate, mission, removeClouds):
  """
  Creates Earth Engine invocation for mean radiance values within a fixed
  geometry over an image collection (optionally applies cloud mask first)
  and also grabs atmospheric correction inputs
  """

  # initialize

  # time and a place
  TimeSeries.geom = geom
  TimeSeries.startDate = ee.Date(startDate)
  TimeSeries.stopDate = ee.Date(stopDate)

  # satellite mission
  TimeSeries.mission = mission
  
  # cloud removal
  TimeSeries.removeClouds = removeClouds
  TimeSeries.cloudRemover = CloudRemover  

  # Earth Engine image collection
  ic = ee.ImageCollection(mission_specifics.eeCollection(mission))\
    .filterBounds(geom)\
    .filterDate(startDate, stopDate)\
    .filter(mission_specifics.sunAngleFilter(mission))

  # data to be extracted (chronological)
  data = ic.map(TimeSeries.extractor).sort('timestamp')

  return ee.FeatureCollection(data)