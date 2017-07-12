"""
cloudRemover.py, Sam Murphy (2017-07-11)

Collection of cloud removal methods for Sentinel 2 and Landsat

for details: https://github.com/samsammurphy/cloud-masking-sentinel2
"""

# Google Earth Engine Python Client API
import ee

class CloudRemover:
  """
  Collection of cloud removal methods for Sentinel 2 and Landsat

  for details: https://github.com/samsammurphy/cloud-masking-sentinel2
  """

  def rescale(img, thresholds):
    """
    Linear stretch of image between two threshold values.
    """
    return img.subtract(thresholds[0]).divide(thresholds[1] - thresholds[0])
  
  def sentinelCloudScore(img):
    """
    Computes spectral indices of cloudyness and take the minimum of them.
    
    Each spectral index is fairly lenient because the group minimum 
    is a somewhat stringent comparison policy. side note -> this seems like a job for machine learning :)
    
    originally written by Matt Hancher for Landsat imagery
    adapted to Sentinel by Chris Hewig and Ian Housman
    """
    
    # cloud until proven otherwise
    score = ee.Image(1)

    # clouds are reasonably bright
    score = score.min(rescale(img.select(['blue']), [0.1, 0.5]))
    score = score.min(rescale(img.select(['aerosol']), [0.1, 0.3]))
    score = score.min(rescale(img.select(['aerosol']).add(img.select(['cirrus'])), [0.15, 0.2]))
    score = score.min(rescale(img.select(['red']).add(img.select(['green'])).add(img.select('blue')), [0.2, 0.8]))

    # clouds are moist
    ndmi = img.normalizedDifference(['red4','swir1'])
    score=score.min(rescale(ndmi, [-0.1, 0.1]))

    # clouds are not snow.
    ndsi = img.normalizedDifference(['green', 'swir1'])
    score=score.min(rescale(ndsi, [0.8, 0.6])).rename(['cloudScore'])
    
    return score
  
  def ESAcloudMask(img):
    """
    European Space Agency (ESA) clouds from 'QA60', i.e. Quality Assessment band at 60m
     
    parsed by Nick Clinton
    """

    qa = img.select('QA60')

    # bits 10 and 11 are clouds and cirrus
    cloudBitMask = int(2**10)
    cirrusBitMask = int(2**11)

    # both flags set to zero indicates clear conditions.
    clear = qa.bitwiseAnd(cloudBitMask).eq(0).And(\
           qa.bitwiseAnd(cirrusBitMask).eq(0))
    
    # clouds are not clear
    cloud = clear.Not().rename(['ESA_clouds'])

    # return the masked and scaled data.
    return cloud

  def shadowMask(img,cloudMask):    
    """
    Finds cloud shadows in images
    
    Originally by Gennadii Donchyts, adapted by Ian Housman
    """
    
    def potentialShadow(cloudHeight):
        """
        Finds potential shadow areas from array of cloud heights
        
        returns an image stack (i.e. list of images) 
        """
        cloudHeight = ee.Number(cloudHeight)
        
        # shadow vector length
        shadowVector = zenith.tan().multiply(cloudHeight)
        
        # x and y components of shadow vector length
        x = azimuth.cos().multiply(shadowVector).divide(nominalScale).round()
        y = azimuth.sin().multiply(shadowVector).divide(nominalScale).round()
        
        # affine translation of clouds
        cloudShift = cloudMask.changeProj(cloudMask.projection(), cloudMask.projection().translate(x, y)) # could incorporate shadow stretch?
        
        return cloudShift
     
    # make sure it is binary (i.e. apply threshold to cloud score)
    cloudScoreThreshold = 0.5
    cloudMask = cloudMask.gt(cloudScoreThreshold)

    # solar geometry (radians)
    azimuth = ee.Number(img.get('solar_azimuth')).multiply(math.pi).divide(180.0).add(ee.Number(0.5).multiply(math.pi))
    zenith  = ee.Number(0.5).multiply(math.pi ).subtract(ee.Number(img.get('solar_zenith')).multiply(math.pi).divide(180.0))

    # find potential shadow areas based on cloud and solar geometry
    nominalScale = cloudMask.projection().nominalScale()
    cloudHeights = ee.List.sequence(500,4000,500)        
    potentialShadowStack = cloudHeights.map(potentialShadow)
    potentialShadow = ee.ImageCollection.fromImages(potentialShadowStack).max()

    # shadows are not clouds
    potentialShadow = potentialShadow.And(cloudMask.Not())

    # (modified) dark pixel detection 
    darkPixels = toa.normalizedDifference(['green', 'swir2']).gt(0.25)

    # shadows are dark
    shadows = potentialShadow.And(darkPixels).rename(['shadows'])
    
    # might be scope for one last check here. Dark surfaces (e.g. water, basalt, etc.) cause shadow commission errors.
    # perhaps using a NDWI (e.g. green and nir)

    return shadows
     
  def sentinel2(image):
    """
    Remove cloud pixels from Sentinel 2 imagery
    """

    # top of atmosphere reflectance
    toa = img.select(['B1','B2','B3','B4','B6','B8A','B9','B10', 'B11','B12'],\
      ['aerosol', 'blue', 'green', 'red', 'red2','red4','h2o', 'cirrus','swir1', 'swir2'])\
      .divide(10000).addBands(img.select('QA60'))\
      .set('solar_azimuth',img.get('MEAN_SOLAR_AZIMUTH_ANGLE'))\
      .set('solar_zenith',img.get('MEAN_SOLAR_ZENITH_ANGLE'))

    # ESA cloud mask
    ESA_clouds = ESAcloudMask(toa)

    # # Sentinel 2 cloud score
    # cloudScore = sentinelCloudScore(toa)
    
    # # Cloud shadow
    # shadows = shadowMask(toa,'cloudScore')
    
    # clear pixels are not cloudy
    clear = ESA_clouds.Not()
    
    # cloud free
    cloudFree = image.updateMask(clear)
    
    return cloudFree
  
  def landsat(image):
    """
    Removes cloud pixels from Landsat image using FMASK band

    NB. calculated on the fly, might be slow
    """
    
    fmask = image.select('fmask')
    # 0 = clear
    # 1 = water
    # 2 = shadow
    # 3 = snow
    # 4 = cloud
    
    # cloud and shadow
    cloud = fmask.eq(4)
    shadow = fmask.eq(2)

    # cloud and shadow remover
    mask = cloud.Or(shadow).eq(0)
    
    return image.updateMask(mask)
  
  def method(mission, cloudMaskType):
    
    # Sentinel 2 has a chose of cloud masks
    if mission == 'Sentinel2':
      
      switch = {
        'QA60': CloudRemover.sentinel2 ,
        'cloudScore': CloudRemover.sentinel2
      }
      return switch[cloudMaskType]

    # Landsat uses FMASK (might add options later)
    else:
      switch = {
        'Landsat8':CloudRemover.landsat,
        'Landsat7':CloudRemover.landsat,
        'Landsat5':CloudRemover.landsat,
        'Landsat4':CloudRemover.landsat
      }
      return switch[mission]