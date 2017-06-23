"""
ee_requests.py, Sam Murphy (2017-06-22)

Set's up batch requests for reduced data from Earth Engine.

Returns a feature collection which could be input into, for exampled:

 - export (e.g to csv)
 - getInfo (e.g. for usage in a notebook with less end-user hoops to jump through)

..depending on workflow
"""

import ee

class CloudRemover:
  """
  Collection of methods for cloud removal from imagery of different satellite missions
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
    Removes cloud pixels from Landsat imagery using FMASK band
    """
    
    # read fmask band
    
    return

class TimeSeries:
  """
  This class is used to extract cloud-free, mean pixel values within
  a given earth engine geometry over an image collection
  """
   
  def extractor(image):
    
    cloud_free = TimeSeries.cloudRemover(image)
    
    properties = {
      'mean_averages':cloud_free.reduceRegion(\
          reducer = ee.Reducer.mean(),\
          geometry = TimeSeries.geom.centroid()),
    }


    return ee.Feature(TimeSeries.geom, properties)
  
  

def request_cloudfree_averages(ic, geom):
  """
  Sets the user-defined geometry to the TimeSeries class, and extracts 
  mean pixel values inside that geometry for all images in a collection
  """
  
  TimeSeries.geom = geom

  TimeSeries.cloudRemover = CloudRemover.sentinel2
  
  return ic.map(TimeSeries.extractor)
