
import math
import pandas as pd

import interpolated_lookup_tables as iLUT
from mission_specifics import common_bandnames, ee_bandnames, py6s_bandnames

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
  elliptical_orbit_correction = 0.03275104*math.cos(math.radians(float(row['doy'])/1.04137484)) + 0.96804905
  
  # correction coefficients
  a = perihelion[0] * elliptical_orbit_correction
  b = perihelion[1] * elliptical_orbit_correction

  # surface reflectance
  try:
    SR = (radiance - a) / b
  except:
    SR = None

  return (SR, a, b)

def bandname_translator(mission, band):
    
    i = common_bandnames(mission).index(band)
    ee_bandname = ee_bandnames(mission)[i]
    py6s_bandname = py6s_bandnames(mission)[i]

    return (ee_bandname, py6s_bandname)

def iLUT_handler(df):
  
  iLUTs = {}
  
  missions = df.mission.unique()
  
  for mission in missions:
    these_iLUTs = iLUT.handler(mission)
    these_iLUTs.get()
    iLUTs[mission] = these_iLUTs.iLUTs
  
  return iLUTs

def add_atmcorr_to_df(atmcorr, df):

  # dataframe format
  SR = pd.DataFrame(x[0] for x in atmcorr)
  coeffs = pd.DataFrame(x[1] for x in atmcorr)

  # time index
  SR.index = df.index
  coeffs.index = df.index

  return pd.concat([df, SR, coeffs], axis=1)

def run_atmcorr(df, force=False):
  
  # already corrected?
  if 'blue' in df.columns.tolist() and not force:
    print("Surface reflectance already calculated")
    print('if override required --> data = run_atmcorr(data, force=True)')
    return df

  atmcorr = []
  iLUTs = iLUT_handler(df)

  print('Calculating surface reflectance')
  for index, row in df.iterrows():

    SRs = {}
    coeffs = {}

    for band in ['blue','green','red','nir','swir1','swir2']:
      
      mission = row['mission']
      ee_bandname, py6s_bandname = bandname_translator(mission, band)
      
      radiance = row[ee_bandname]
      iLUT = iLUTs[mission][py6s_bandname]

      SR, a, b = surface_reflectance(radiance, iLUT, row)

      SRs[band] = SR
      coeffs[band+'_coeffs'] = (a, b)

    atmcorr.append((SRs, coeffs))

  df = add_atmcorr_to_df(atmcorr, df)

  return df