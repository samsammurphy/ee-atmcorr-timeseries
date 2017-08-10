"""
Reads kml files
"""

import os
import ee
from fastkml import kml
    
def read_kml(fileName, polygonName):
  """
  Atmospherically corrects radiance using correction coefficients
  at perihelion adjusted for Earth's ellipitcal orbit
  """
 
  # read kml from file 
  try:
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    fpath = os.path.join(base_dir,'files','kml',fileName)
    with open(fpath,'rb') as file:
      kml_string = file.read()
  except:
    print('problem loading kml file: \n'+fpath)
    return

  # kml object
  k = kml.KML()
  k.from_string(kml_string)

  # parse the object
  document = list(k.features())
  folder = list(document[0].features())
  polygons = list(folder[0].features())
  names = [p.name for p in polygons]

  # find polygon
  polygon = polygons[names.index(polygonName)].geometry

  # get coordinates
  coords = polygon.exterior.coords

  # create list of lonlat points
  lon = [x[0] for x in coords]
  lat = [x[1] for x in coords]
  lonlat = [x for t in zip(lon,lat) for x in t]

  # earth engine geometry
  return ee.Geometry.Polygon(lonlat)
