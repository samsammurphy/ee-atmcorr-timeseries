
from mission_specifics import common_bandnames, ee_bandnames, py6s_bandnames
import interpolated_lookup_tables as iLUT
import math


def find_unique_missions(df):
  
  return ['Landsat4','Landsat5','Landsat7','Landsat8','Sentinel2']

def iLUT_handler(df):
  
  iLUTs = {}
  
  missions = find_unique_missions(df)
  
  for mission in missions:
    these_iLUTs = iLUT.handler(mission)
    these_iLUTs.get()
    iLUTs[mission] = these_iLUTs.iLUTs
  
  return iLUTs

def surface_reflectance(radiance, iLUT, row):
  """
  Atmospherically corrects radiance using correction coefficients
  at perihelion adjusted for Earth's ellipitcal orbit
  """
  
  # correction coefficients at perihelion
  perihelion = iLUT(row['solar_z'], 
                    row['h2o'], 
                    row['o3'], 
                    row['aot'], 
                    row['alt'])

  # elliptical orbit correction
  elliptical_orbit_correction = 0.03275104*math.cos(math.radians(row['doy']/1.04137484)) + 0.96804905
  
  # correction coefficients
  a = perihelion[0] * elliptical_orbit_correction
  b = perihelion[1] * elliptical_orbit_correction

  # surface reflectance
  try:
    SR = (radiance - a) / b
  except:
    SR = None

  return {'SR':SR, 'a':a, 'b':b}

def bandname_translator(mission, band):
    
    i = common_bandnames[mission].index(band)
    ee_bandname = ee_bandnames[mission][i]
    py6s_bandname = py6s_bandnames[mission][i]

    return (ee_bandname, py6s_bandname)

def run_atmcorr(df):

  # surface reflectances time series
  SR_timeseries = []

  # interpolated lookup tables
  iLUTs = iLUT_handler(df)

  # iterate through input dataframe
  # for index, row in df.iterrows():
  #   x = row['column_name']

  # surface reflectances for this scene
  SR_and_coeffs = {}

  for band in ['blue','green','red','nir','swir1','swir2']:
    
    ee_bandname, py6s_bandname = bandname_translator(mission, band)
    
    radiance = row[ee_bandname]
    iLUT = iLUTs[mission][py6s_bandname]

    SR_and_coeffs[band] = surface_reflectance(radiance, iLUT, row)
  
  # add to list
  SR_timeseries.append(SR_and_coeffs)

  # add surface reflectance to dataframe
  # format = metadata + SR + rest

  return df