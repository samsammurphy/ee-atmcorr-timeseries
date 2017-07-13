"""
interpolated_lookup_tables.py, Sam Murphy (2017-06-22)


The interpolated_lookup_table.handler manages loading, downloading 
and interpolating the look up tables used by the 6S emulator 

"""

import os
import sys
import glob
import pickle
import urllib.request
import zipfile
import time
from itertools import product
from scipy.interpolate import LinearNDInterpolator
import mission_specifics

class handler:
  """
  The interpolated_lookup_table.handler manages loading, downloading 
  and interpolating the look up tables used by the 6S emulator 
  """
  
  def __init__(self, mission, path=False):
   
    self.userDefinedPath = path
    self.mission = mission
    self.supportedMissions = ['Sentinel2', 'Landsat8', 'Landsat7', 'Landsat5', 'Landsat4']
    
    # default file paths
    self.bin_path = os.path.dirname(os.path.abspath(__file__))
    self.base_path = os.path.dirname(self.bin_path)
    self.files_path = os.path.join(self.base_path,'files')
    self.py6S_sensor = mission_specifics.py6S_sensor(self.mission)
    self.LUT_path = os.path.join(self.files_path,'LUTs',self.py6S_sensor,\
        'Continental','view_zenith_0')
    self.iLUT_path = os.path.join(self.files_path,'iLUTs',self.py6S_sensor,\
        'Continental','view_zenith_0')
  
  def download_LUTs(self):
    """
    Downloads the look-up tables for a given satellite mission
    """
    
    # directory for zip file
    zip_dir = os.path.join(self.files_path,'LUTs')
    if not os.path.isdir(zip_dir):
      os.makedirs(zip_dir)

    # Sentinel 2 and Landsats URL switch
    getURL = {
      'S2A_MSI':"https://www.dropbox.com/s/aq873gil0ph47fm/S2A_MSI.zip?dl=1",
      'LANDSAT_OLI':'https://www.dropbox.com/s/49ikr48d2qqwkhm/LANDSAT_OLI.zip?dl=1',
      'LANDSAT_ETM':'https://www.dropbox.com/s/z6vv55cz5tow6tj/LANDSAT_ETM.zip?dl=1',
      'LANDSAT_TM':'https://www.dropbox.com/s/uyiab5r9kl50m2f/LANDSAT_TM.zip?dl=1',
      'LANDSAT_TM':'https://www.dropbox.com/s/uyiab5r9kl50m2f/LANDSAT_TM.zip?dl=1'
    }

    # download LUTs data
    print('downloading look up table (.lut) files..')
    url = getURL[self.py6S_sensor]
    u = urllib.request.urlopen(url)
    data = u.read()
    u.close()
    
    # save to zip file
    zip_filepath = os.path.join(zip_dir,self.py6S_sensor+'.zip')
    with open(zip_filepath, "wb") as f :
        f.write(data)

    # extract LUTs directory
    with zipfile.ZipFile(zip_filepath,"r") as zip_ref:
        zip_ref.extractall(zip_dir)

    # delete zip file
    os.remove(zip_filepath)

    print('download successful')
  
  
  def interpolate_LUTs(self):
    """
    interpolates look up table files (.lut)
    """

    filepaths = sorted(glob.glob(self.LUT_path+os.path.sep+'*.lut'))
    if filepaths:
      print('\n...Running n-dimensional interpolation may take a several minutes (only need to do this once)...')
      try:
        for fpath in filepaths:
          fname = os.path.basename(fpath)
          fid, ext = os.path.splitext(fname)
          ilut_filepath = os.path.join(self.iLUT_path,fid+'.ilut')
          if os.path.isfile(ilut_filepath):
            print('iLUT file already exists (skipping interpolation): {}'.format(fname))
          else:
            print('Interpolating: '+fname)
            
            # load look up table
            LUT = pickle.load(open(fpath,"rb"))

            # input variables (all permutations)
            invars = LUT['config']['invars']
            inputs = list(product(invars['solar_zs'],
                                  invars['H2Os'],
                                  invars['O3s'],
                                  invars['AOTs'],
                                  invars['alts']))  
            
            # output variables (6S correction coefficients)
            outputs = LUT['outputs']

            # piecewise linear interpolant in n-dimensions
            t = time.time()
            interpolator = LinearNDInterpolator(inputs,outputs)
            print('Interpolation took {:.2f} (secs) = '.format(time.time()-t))
            
            # save new interpolated LUT file
            pickle.dump(interpolator, open(ilut_filepath, 'wb' ))

      except:

        print('interpolation error')

    else:
      
      print('look up tables files (.lut) not found in LUTs directory:\n{}'.format(self.LUT_path))

  def load_iluts_from_path(self):
    """
    looks for .ilut files in self.iLUT_path and loads them into self.iLUTs
    """
    
    print('Loading interpolated look up tables (.ilut)..')

    ilut_files = glob.glob(self.iLUT_path+os.path.sep+'*.ilut')
    if ilut_files:
      try:
        for f in ilut_files:
          bandName_py6s = os.path.basename(f).split('.')[0][-2:]
          self.iLUTs[bandName_py6s] = pickle.load(open(f,'rb'))
        print('Success')
        return
      except:
        print('error loading file: \n'+f)      
    else:
      print('Interpolated look-up table files not found in:\n{}'.format(self.iLUT_path))

  def load_iluts_from_mission(self):
    """
    1) loads iLUTs from default path
    2) else, downloads look-up tables and interpolates them.
    """

    # check satellite mission is supported
    if self.mission.title() not in self.supportedMissions:
      print("mission '{0.mission}' not in supported missions:\n{0.supportedMissions}".format(self))
      sys.exit(1)
    else:
      # use standardized format internally
      self.mission = self.mission.title()
   
    # try loading from default first
    try:
      self.load_iluts_from_path()
    except:
      pass

  def get(self):
    """
    
    Loads interpolated look-up files in one of two ways:

    1) if self.iLUT_path is defined:

       - load all .ilut files in that path
    
    2) if self.mission is defined:

       - download lut files (i.e. look-up tables)
       - interpolate lut files (creating ilut files; note new 'i' prefix)
       - load the ilut files

    """
    
    # create iLUTs dictionary
    self.iLUTs = {}

    # try loading from user defined-path
    if self.userDefinedPath:
      self.iLUT_path = self.userDefinedPath
      self.load_iluts_from_path() 
      return

    # create default file paths?
    if not os.path.isdir(self.files_path):
      os.makedirs(self.files_path)
    if not os.path.isdir(self.LUT_path):
      os.makedirs(self.LUT_path)
    if not os.path.isdir(self.iLUT_path):
        os.makedirs(self.iLUT_path)

    # search default file paths for this mission
    if self.mission:
      self.load_iluts_from_mission()
      if self.iLUTs:
        return

    # try downloading? 
    try:
      self.download_LUTs()
      self.interpolate_LUTs()
      self.load_iluts_from_path()
    except:
      pass

    # otherwise return error
    if not self.iLUT_path or not self.mission:
      print('must define self.path or self.mission of iLUT.handler() instance')
      sys.exit(1)



# debugging
# iLUTs = handler() 
# iLUTs.mission = 'Landsat7'
# iLUTs.get()
# print(iLUTs.iLUTs)