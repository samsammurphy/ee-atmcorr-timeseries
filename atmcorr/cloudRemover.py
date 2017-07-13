"""
cloudRemover.py, Sam Murphy (2017-07-11)

Collection of cloud removal methods for Sentinel 2 and Landsat

for details: https://github.com/samsammurphy/cloud-masking-sentinel2
"""

import ee
import math

def ESAclouds(toa):
    """
    European Space Agency (ESA) clouds from 'QA60', i.e. Quality Assessment band at 60m

    parsed by Nick Clinton
    """

    qa = toa.select('QA60')

    # bits 10 and 11 are clouds and cirrus
    cloudBitMask = int(2**10)
    cirrusBitMask = int(2**11)

    # both flags set to zero indicates clear conditions.
    clear = qa.bitwiseAnd(cloudBitMask).eq(0).And(\
           qa.bitwiseAnd(cirrusBitMask).eq(0))

    # cloud is not clear
    cloud = clear.eq(0)

    return cloud

def shadowMask(toa,cloudMask):
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

    # solar geometry (radians)
    azimuth = ee.Number(toa.get('solar_azimuth')).multiply(math.pi).divide(180.0).add(ee.Number(0.5).multiply(math.pi))
    zenith  = ee.Number(0.5).multiply(math.pi ).subtract(ee.Number(toa.get('solar_zenith')).multiply(math.pi).divide(180.0))

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
    shadow = potentialShadow.And(darkPixels).rename(['shadows'])

    # might be scope for one last check here. Dark surfaces (e.g. water, basalt, etc.) cause shadow commission errors.
    # perhaps using a NDWI (e.g. green and nir)

    return shadow

#

class CloudRemover:
  
  ESAclouds = ESAclouds
  shadowMask = shadowMask

  def sentinel2mask(img):
    """
    Masks cloud (and shadow) pixels from Sentinel 2 image
    """
      
    # top of atmosphere reflectance
    toa = img.select(['B1','B2','B3','B4','B6','B8A','B9','B10', 'B11','B12'],\
      ['aerosol', 'blue', 'green', 'red', 'red2','red4','h2o', 'cirrus','swir1', 'swir2'])\
      .divide(10000).addBands(img.select('QA60'))\
      .set('solar_azimuth',img.get('MEAN_SOLAR_AZIMUTH_ANGLE'))\
      .set('solar_zenith',img.get('MEAN_SOLAR_ZENITH_ANGLE'))
                  
    # ESA clouds
    ESAcloud = CloudRemover.ESAclouds(toa)

    # Shadow
    shadow = CloudRemover.shadowMask(toa, ESAcloud)

    # cloud and shadow mask
    mask = ESAcloud.Or(shadow).eq(0)

    return img.updateMask(mask)
  
  def landsatMask(img):
    """
    Masks cloud (and shadow) pixels from Landsat images
    """
    
    # FMASK
    fmask = img.select('fmask')
    
    # cloud and shadow
    cloud = fmask.eq(4)
    shadow = fmask.eq(2)
    
    # cloudFree pixels are not cloud or shadow
    cloudFree = cloud.Or(shadow).eq(0)
    
    return img.updateMask(cloudFree)
  
  def fromMission(mission):
    
    switch = {
      'sentinel2': CloudRemover.sentinel2mask,
      'landsat8': CloudRemover.landsatMask,
      'landsat7': CloudRemover.landsatMask,
      'landsat5': CloudRemover.landsatMask,
      'landsat4': CloudRemover.landsatMask,
    }

    return switch[mission.lower()]


  
  
