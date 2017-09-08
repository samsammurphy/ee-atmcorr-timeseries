"""
Functionality for finding and viewing images in time series 
"""

import math
import ee
from ast import literal_eval as make_tuple
from IPython.display import Image

import mission_specifics
from mission_specifics import eeCollection, common_bandnames, ee_bandnames

def find_scene_by_date(df, date):
  
  filtered = df.dropna(subset=['blue'])
  after_date = filtered[filtered.index >= date]

  scene = after_date.iloc[0]

  scene_datetime = str(after_date.index[0].to_pydatetime())
  fileID = scene['imageID']

  print('scene datetime: '+scene_datetime)
  print('fileID: '+fileID)

  return scene

def find_scene(df, date, fileID):
    
    if date:
        scene = find_scene_by_date(df, date)
#     elif fileID:
#         scene = find_scene_by_fileId(df, fileID)
#     else:
#         scene = first_non_null_scene()
        
    return scene

def radianceFromTOA(img, scene):
  """
  calculate at-sensor radiance from top-of-atmosphere (TOA) reflectance

  (Sentinel 2 and Landsat_FMASK support)
  """

  # scene metadata
  mission = scene['mission']
  day_of_year = scene['doy']
  bands = mission_specifics.ee_bandnames(mission)

  # solar irradiance, zenith and distance
  ESUNs = mission_specifics.ESUNs(img, mission)
  theta = mission_specifics.solar_z(img, mission).multiply(0.017453293)
  d = ee.Number(day_of_year).subtract(4).multiply(0.017202).cos().multiply(-0.01672).add(1)
  d_squared = d.multiply(d)

  # toa correction (Sentinel 2)
  toa = mission_specifics.TOA(img, mission)# (i.e. apply Sentinel 2 correction)

  # radiance at-sensor
  rad = toa.select(ee.List(bands)).multiply(ESUNs).multiply(theta.cos()).divide(math.pi).divide(d_squared)

  return rad

def tuple_format(obj):
  
  if isinstance(obj, tuple):
    return obj
  else:
    return make_tuple(obj)
  
def apply_coefficients(rad, scene, band):
  """
  Applies coefficients to single waveband
  """
  
  i = common_bandnames(scene['mission']).index(band)
  ee_bandname = ee_bandnames(scene['mission'])[i]

  coeffs = tuple_format(scene[band+'_coeffs'])
  a = coeffs[0]
  b = coeffs[1]

  SR = rad.select(ee_bandname).subtract(a).divide(b).rename([band])
  
  return SR

def surface_reflectance_image(scene, bands):
    
    # earth engine radiance image
    assetID = eeCollection(scene['mission']) + '/' + scene['imageID']
    toa = ee.Image(assetID)
    rad = radianceFromTOA(toa, scene)

    # assign earthengine bandnames to rgb output
    rr = apply_coefficients(rad, scene, bands[0])
    gg = apply_coefficients(rad, scene, bands[1])
    bb = apply_coefficients(rad, scene, bands[2])
    
    return rr.addBands(gg).addBands(bb)


def surface_reflectance_inspector(df, date=False, fileID=False, bands=False):

    scene = find_scene(df, date, fileID)

    SR_image = surface_reflectance_image(scene, bands)
    
    return SR_image

def rgb_to_pureHue(rgb):
  hsv = rgb.rgbToHsv()
  hue = hsv.select('hue')
  purehue = hue.addBands(ee.Image(1)).addBands(ee.Image(1)).hsvToRgb()
  return purehue

def view_window(geom):
    
    # geometry based
    length_scale = geom.area().sqrt()
    geom_based = geom.centroid().buffer(length_scale.multiply(3))
    
    # minimum size = 1km
    minimum = geom.centroid().buffer(1000)
    
    # comparison
    c = geom_based.area().gt(minimum.area())
    
    window = ee.Algorithms.If(c, geom_based, minimum)
    
    # jupyter notebook will require view window coordinates locally
    return window.getInfo()['coordinates']