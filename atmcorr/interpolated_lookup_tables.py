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

# import mission_specifics

class handler:
  """
  The interpolated_lookup_table.handler manages loading, downloading 
  and interpolating the look up tables used by the 6S emulator 
  """
  
  def __init__(self, mission=False, path=False):
   
    self.path = path
    self.mission = mission
    self.supportedMissions = ['Sentinel2']

    # mission specific
    ##############################################################################
    self.py6S_sensor = 'S2A_MSI'#mission_specifics.py6S_sensor(mission)
    ##############################################################################

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

    print('downloaded successful')
  
  
  def interpolate_LUTs(self):
    """
    interpolates look up table files (.lut)
    """

    filepaths = sorted(glob.glob(self.LUT_path+os.path.sep+'*.lut'))
    if filepaths:
      print('running n-dimensional interpolation may take a few minutes...(only need to do this once per mission).')
      try:
        for fpath in filepaths:
          fname = os.path.basename(fpath)
          fid, ext = os.path.splitext(fname)
          ilut_filepath = os.path.join(self.path,fid+'.ilut')
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
    looks for .ilut files in self.path and loads them into self.iLUTs
    """
    
    print('loading interpolated look up tables (.ilut) from :...\n{}'.format(self.path))

    ilut_files = glob.glob(self.path+os.path.sep+'*.ilut')
    if ilut_files:
      try:
        for f in ilut_files:
          bandName_py6s = os.path.basename(f).split('.')[0][-2:]
          self.iLUTs[bandName_py6s] = pickle.load(open(f,'rb'))
        print('success')
        return
      except:
        print('error: loading file: \n'+f)      
    else:
      print('error: interpolated look-up table files (.ilut) not found')

  def load_iluts_from_mission(self):
    """
    downloads look-up tables for a given mission and interpolates them.
    """
    
    # default file paths
    self.bin_path = os.path.dirname(os.path.abspath(__file__))
    self.base_path = os.path.dirname(self.bin_path)
    self.files_path = os.path.join(self.base_path,'files')
    
    self.LUT_path = os.path.join(self.files_path,'LUTs',self.py6S_sensor,\
      'Continental','view_zenith_0')
    self.path = os.path.join(self.files_path,'iLUTs',self.py6S_sensor,\
     'Continental','view_zenith_0')

    # create default file paths
    if not os.path.isdir(self.files_path):
      os.makedirs(self.files_path)
    if not os.path.isdir(self.LUT_path):
      os.makedirs(self.LUT_path)
    if not os.path.isdir(self.path):
        os.makedirs(self.path)
   
    # download the files
    self.download_LUTs()

    # interpolate them
    self.interpolate_LUTs()

    # load files
    self.load_iluts_from_path()

  def get(self):
    """
    
    Loads interpolated look-up files in one of two ways:

    1) if self.path is defined:

       - load all .ilut files in that path
    
    2) if self.mission is defined:

       - download lut files (i.e. look-up tables)
       - interpolate lut files (creating ilut files; note new 'i' prefix)
       - load the ilut files

    """
    
    # create iLUTs dictionary
    self.iLUTs = {}

    # try loading from path (if defined)
    if self.path:
      self.load_iluts_from_path() 
      
      # if iluts loaded correctly then we're good
      if self.iLUTs:
        return

    # otherwise, try downloading and interpolating
    if self.mission:
      self.load_iluts_from_mission() # mission not supported: options include ['Sentinel2']

      if not self.iLUTs:
        print('fatal error: interpolated look up tables have not been loaded successfully!')
        sys.exit(1)

    # check path or mission were defined
    if not self.path and not self.mission:
      print('fatal error: must define self.path or self.mission for iLUT.handler() instance')
      sys.exit(1)


# # debugging
# iLUTs = handler() 
# iLUTs.mission = 'Sentinel2'
# iLUTs.get()
# print(iLUTs.iLUTs)