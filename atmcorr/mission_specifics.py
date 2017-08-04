"""
mission_specifics.py, Sam Murphy (2017-06-28)

Information on satellite missions stored here (e.g. wavebands, etc.)
"""

import ee


def ee_bandnames(mission):
  """
  visible to short-wave infrared wavebands (EarthEngine nomenclature)

  notes:
    [1] skipped Landsat7 'PAN' to fit Py6S
  """

  switch = {
    'Sentinel2':['B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B10','B11','B12'],
    'Landsat8':['B1','B2','B3','B4','B5','B6','B7','B8','B9'],
    'Landsat7':['B1','B2','B3','B4','B5','B7'],
    'Landsat5':['B1','B2','B3','B4','B5','B7'],
    'Landsat4':['B1','B2','B3','B4','B5','B7']
  }

  return switch[mission]

def py6s_bandnames(mission):
  """
  visible to short-wave infrared wavebands (Py6S nomenclature)

  notes: 
    [1] Landsat8 'B8' === 'PAN'
    [2] Landsat7 'PAN' is missing?

  """

  switch = {
    'Sentinel2':['01','02','03','04','05','06','07','08','09','10','11','12','13'],
    'Landsat8':['B1','B2','B3','B4','B5','B6','B7','B8','B9'],
    'Landsat7':['B1','B2','B3','B4','B5','B7'],
    'Landsat5':['B1','B2','B3','B4','B5','B7'],
    'Landsat4':['B1','B2','B3','B4','B5','B7']
  }

  return switch[mission]

def common_bandnames(mission):
  """
  visible to short-wave infrared wavebands (common bandnames)
  """

  switch = {
    'Sentinel2':['aerosol','blue','green','red',
    'redEdge1','redEdge2','redEdge3','nir','redEdge4',
    'waterVapour','cirrus','swir1','swir2'],
    'Landsat8':['aerosol','blue','green','red','nir','swir1','swir2','pan','cirrus'],
    'Landsat7':['blue','green','red','nir','swir1','swir2'],
    'Landsat5':['blue','green','red','nir','swir1','swir2'],
    'Landsat4':['blue','green','red','nir','swir1','swir2']
  }

  return switch[mission]

def py6S_sensor(mission):
  """
  Py6S satellite_sensor name from satellite mission name
  """
  
  switch = {
    'Sentinel2':'S2A_MSI',
    'Landsat8':'LANDSAT_OLI',
    'Landsat7':'LANDSAT_ETM',
    'Landsat5':'LANDSAT_TM',
    'Landsat4':'LANDSAT_TM'
  }

  return switch[mission]

def eeCollection(mission):
  """
  Earth Engine image collection name from satellite mission name
  """

  switch = {
    'Sentinel2':'COPERNICUS/S2',
    'Landsat8':'LANDSAT/LC8_L1T_TOA_FMASK',
    'Landsat7':'LANDSAT/LE7_L1T_TOA_FMASK',
    'Landsat5':'LANDSAT/LT5_L1T_TOA_FMASK',
    'Landsat4':'LANDSAT/LT4_L1T_TOA_FMASK'
  }

  return switch[mission]

def sunAngleFilter(mission):
  """
  Sun angle filter avoids where elevation < 15 degrees
  """
  
  switch = {
    'Sentinel2':ee.Filter.lt('MEAN_SOLAR_ZENITH_ANGLE',75),
    'Landsat8':ee.Filter.gt('SUN_ELEVATION',15),
    'Landsat7':ee.Filter.gt('SUN_ELEVATION',15),
    'Landsat5':ee.Filter.gt('SUN_ELEVATION',15),
    'Landsat4':ee.Filter.gt('SUN_ELEVATION',15)
  }

  return switch[mission]

def ESUNs(img, mission):
  """
  ESUN (Exoatmospheric spectral irradiance)

  References
  ----------

  Landsat 4  [1]
  Landsat 5  [1]
  Landsat 7  [1]
  Landsat 8  [2]


  [1] Chander et al. (2009) Summary of current radiometric calibration
      coefficients for Landsat MSS, TM, ETM+, and EO-1 ALI sensors.
      Remote Sensing of Environment. 113, 898-903

  [2] Benjamin Leutner (https://github.com/bleutner/RStoolbox)
  """

  sentinel2 =  ee.Image([
      ee.Number(img.get('SOLAR_IRRADIANCE_B1')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B2')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B3')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B4')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B5')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B6')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B7')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B8')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B8A')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B9')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B10')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B11')),
      ee.Number(img.get('SOLAR_IRRADIANCE_B12'))
    ])

  Landsat8 = ee.Image([1895.33, 2004.57, 1820.75, 1549.49, 951.76, 247.55, 85.46, 1723.8, 366.97])
  Landsat7 = ee.Image([1997, 1812, 1533, 1039, 230.8, 84.9]) # PAN =  1362 (removed to match Py6S)
  Landsat5 = ee.Image([1983, 1796, 1536, 1031, 220, 83.44])
  Landsat4 = ee.Image([1983, 1795, 1539, 1028, 219.8, 83.49])

  switch = {
    'Sentinel2':sentinel2,
    'Landsat8':Landsat8,
    'Landsat7':Landsat7,
    'Landsat5':Landsat5,
    'Landsat4':Landsat4
  }

  return switch[mission]

def solar_z(image, mission):
  """
  solar zenith angle (degrees)
  """

  def sentinel2(image):
    return ee.Number(image.get('MEAN_SOLAR_ZENITH_ANGLE'))
  
  def landsat(image):
    return ee.Number(90).subtract(image.get('SUN_ELEVATION'))
  
  switch = {

    'Sentinel2':sentinel2,
    'Landsat8':landsat,
    'Landsat7':landsat,
    'Landsat5':landsat,
    'Landsat4':landsat
  }

  getSolarZenith = switch[mission]

  return getSolarZenith(image)

def TOA(image, mission):

  switch = {

    'Sentinel2':image.divide(10000),
    'Landsat8':image,
    'Landsat7':image,
    'Landsat5':image,
    'Landsat4':image
  }

  return switch[mission]