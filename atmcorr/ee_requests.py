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

ee.Initialize()

class CloudRemover:
  """
  Collection of cloud removal methods for different satellite missions
  """
  
  def sentinel2(image):
    """
    Removes cloud pixels from Sentinel 2 image using QA60 band
    """
    
    cloud = image.select('QA60').gt(0)
    cloudy = cloud.distance(ee.Kernel.euclidean(120, "meters")).gte(0).unmask(0, False)
    cloudFree = image.updateMask(cloudy.eq(0))
    
    return cloudFree
  
  def landsat(image):
    """
    Removes cloud pixels from Landsat image using FMASK band
    """
    
    # read fmask band
    
    return

class RadianceFromTOA:
  """
  Collection of methods to convert top-of-atmosphere (TOA) reflectance
  to at-sensor radiance
  """
  
  def sentinel2(image):
    """
    converts Sentinel2 TOA to at-sensor radiance
    """

    # Top of atmosphere reflectance
    toa = image.divide(10000)

    # solar irradiances
    ESUNs = ee.Image([
      ee.Number(image.get('SOLAR_IRRADIANCE_B1'))#,
      # ee.Number(image.get('SOLAR_IRRADIANCE_B2')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B3')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B4')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B5')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B6')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B7')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B8')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B8A')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B9')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B10')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B11')),
      # ee.Number(image.get('SOLAR_IRRADIANCE_B12'))
    ])

    # wavebands
    bands = ee.List(['B1'])#,'B2','B3','B4','B5','B6','B7','B8','B8A','B9','B10','B11','B12'])

    # solar zenith (radians)
    theta = ee.Number(image.get('MEAN_SOLAR_ZENITH_ANGLE')).multiply(57.295779513)

    # circular math
    pi = ee.Number(3.14159265359)

    # Earth-Sun distance squared (AU)
    day_of_year = 1
    d = ee.Number(day_of_year).subtract(4).multiply(0.017202).cos().multiply(-0.01672).add(1)
    d_squared = d.multiply(d)

    # radiace at-sensor
    rad = toa.select(bands).multiply(ESUNs).multiply(theta.cos()).divide(pi).divide(d_squared)

    return rad
  
  def landsat(image):
    """
    converts Landsat TOA to at-sensor radiance
    """

    # run check that this is TOA_FMASK

    return image


class AtmcorrInput:
  """
  Grabs inputs that are required for atmospheric correction using the 6S emulator
  """

  # global elevation (kilometers)
  elevation = ee.Image('USGS/GMTED2010').divide(1000)

  def get():
    
    altitude = AtmcorrInput.elevation.reduceRegion(\
        reducer = ee.Reducer.mean(),\
        geometry = TimeSeries.geom.centroid()\
        )

    return ee.Dictionary({
      # mission specific!!
      ###########################################################
      'solar_z':AtmcorrInput.image.get('MEAN_SOLAR_ZENITH_ANGLE'),
      ###########################################################
      'h2o':Atmospheric.water(TimeSeries.geom,TimeSeries.date),
      'o3':Atmospheric.ozone(TimeSeries.geom,TimeSeries.date),
      'aot':Atmospheric.aerosol(TimeSeries.geom,TimeSeries.date),
      'alt':altitude.get('be75'),
      'doy':TimeSeries.doy_from_date(TimeSeries.date)
      })
  


class TimeSeries:
  """
  This class is used to extract cloud-free, average radiance values 
  contained within an earth engine geometry for all images in a collection,
  It also gathers the atmospheric correction input variables required to 
  calculate surface reflectance from at-sensor radiance.
  """

  def doy_from_date(date):
    """
    day-of-year from Earth Engine date
    """
    jan01 = ee.Date.fromYMD(date.get('year'),1,1)
    doy = ee.Number(date.difference(jan01,'day')).add(1)
    return doy

  def meanReduce(image, geom):
    """
    Calculates mean average pixel values in a geometry
    """    
    
    mean_averages = image.reduceRegion(\
          reducer = ee.Reducer.mean(),\
          geometry = geom)
    
    return mean_averages
   
  def extractor(image):
    
    # image date
    TimeSeries.date = ee.Date(image.get('system:time_start'))
    
    # remove clouds
    cloudFree = TimeSeries.cloudRemover(image)

    # convert to radiance
    cloudFreeRadiance = TimeSeries.radianceFromTOA(cloudFree)

    # calculate mean averages
    mean_averages = TimeSeries.meanReduce(cloudFreeRadiance, TimeSeries.geom)

    # atmospheric correction inputs
    AtmcorrInput.image = image
    atmcorr_inputs = AtmcorrInput.get()
    
    # # export to new feature collection
    # properties = {
    #   'imgID':image.get('system:index'),
    #   'mean_averages':mean_averages,
    #   'atmcorr_inputs':atmcorr_inputs      
    # }  

    return ee.Feature(TimeSeries.geom, atmcorr_inputs)

def request_cloudFreeRadiance(ic, geom):
  """
  Sets the user-defined geometry to the TimeSeries class, and extracts 
  mean radiance values inside that geometry for all images in a collection
  """
  
  # initialize
  TimeSeries.geom = geom                                 # geometry for pixel averages
  TimeSeries.cloudRemover = CloudRemover.sentinel2       # method for cloud removal
  TimeSeries.radianceFromTOA = RadianceFromTOA.sentinel2 # method for radiance conversion
  
  return ic.map(TimeSeries.extractor)



# # debugging
# # Location and time
# geom = ee.Geometry.Point(-106.597016, 35.196966)
# date = ee.Date('2016-10-01')# will try to find first image from this date

# # Sentinel 2 image
# image = ee.Image(
#   ee.ImageCollection('COPERNICUS/S2')
#     .filterBounds(geom)
#     .filterDate(date,date.advance(3,'month'))
#     .sort('system:time_start')
#     .first()
#   )

# cloudFree = CloudRemover.sentinel2(image)

# rad = RadianceFromTOA.sentinel2(cloudFree)

# mean_averages = rad.reduceRegion(\
#       reducer = ee.Reducer.mean(),\
#       geometry = geom)
