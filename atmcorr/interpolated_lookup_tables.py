"""
interpolated_lookup_tables.py, Sam Murphy (2017-06-22)


The interpolated_lookup_table.handler manages loading, downloading 
and interpolating the look up tables used by the 6S emulator 

"""

import os
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
  
  def __init__(self, imageCollectionID=False, satelliteMission=False, iLUT_path=False):
    
    self.imageCollectionID = imageCollectionID
    self.satelliteMission = satelliteMission
    self.iLUT_path = iLUT_path

    ##############################################################################
    #Earth Engine mission to Py6S sensor name
    self.py6S_sensor = 'S2A_MSI'#mission_specifics.py6S_sensor(imageCollectionID, satelliteMission)
    ##############################################################################
    
    # default file paths
    self.bin_path = os.path.dirname(os.path.abspath(__file__))
    self.base_path = os.path.dirname(self.bin_path)
    self.files_path = os.path.join(self.base_path,'files')
    self.LUT_path = os.path.join(self.files_path,'LUTs',self.py6S_sensor,\
    'Continental','view_zenith_0')
    if not iLUT_path:
      self.iLUT_path = os.path.join(self.files_path,'iLUTs',self.py6S_sensor,\
      'Continental','view_zenith_0')


  def get(self):
    """
    Loads interpolated look-up tables from local files (if they exist)

    else checks for look-up tables (will try downloading if not
    found) and interpolates.
    """
    
    # create iLUTs dictionary
    self.iLUTs = {}

    # see if iLUTs already exists
    ilut_files = glob.glob(self.iLUT_path+os.path.sep+'*.ilut')
    
    if ilut_files:
      
      try:
        
        for f in ilut_files:
          
          bandName_py6s = os.path.basename(f).split('.')[0][-2:]
          self.iLUTs[bandName_py6s] = pickle.load(open(f,'rb'))

        # if iLUTs exists and load properly, then we're good
        return

      except:
        print('loading error for (.ilut) files in:\n'+self.iLUT_path)      
    
    else:
      print('Interpolated look-up tables not found in:\n{}'.format(self.iLUT_path))
      print('Will search for (un-interpolated) look-up tables in:\n{}'.format(self.LUT_path))
    
    return
    
    # else, see if LUTs exists
    # yes, interpolate and return

    # else, 
    # download LUTS
    # interpolate  and return 

    # else,
    # warning!
    # must define one of following: imageCollectionID, satellite_mission, iLUT_path

  def interpolate_LUTs(self):
    """
    interpolate look up tables
    """
    
    filepaths = sorted(glob.glob(self.LUT_path+os.path.sep+'*.lut'))

    if filepaths:
      
      print('running n-dimensional interpolation may take a few minutes...')
      
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
      
      print('LUTs directory: ',self.LUT_path)
      print('LUT files (.lut) not found in LUTs directory, try downloading?')
      

  def download_LUTs(self):
    
    # directory for zip file
    zip_dir = os.path.join(self.files_path,'LUTs')
    if not os.path.isdir(zip_dir):
      os.makedirs(zip_dir)

    # URLs for Sentinel 2 and Landsats (dl=1 is important)
    getURL = {
      'S2A_MSI':"https://www.dropbox.com/s/aq873gil0ph47fm/S2A_MSI.zip?dl=1",
      'LANDSAT_OLI':'https://www.dropbox.com/s/49ikr48d2qqwkhm/LANDSAT_OLI.zip?dl=1',
      'LANDSAT_ETM':'https://www.dropbox.com/s/z6vv55cz5tow6tj/LANDSAT_ETM.zip?dl=1',
      'LANDSAT_TM':'https://www.dropbox.com/s/uyiab5r9kl50m2f/LANDSAT_TM.zip?dl=1',
      'LANDSAT_TM':'https://www.dropbox.com/s/uyiab5r9kl50m2f/LANDSAT_TM.zip?dl=1'
    }

    # download LUTs data
    print('Downloading look up table (LUT) zip file..')
    url = getURL[self.py6S_sensor]
    u = urllib.request.urlopen(url)
    data = u.read()
    u.close()
    
    # save to zip file
    zip_filepath = os.path.join(zip_dir,self.py6S_sensor+'.zip')
    with open(zip_filepath, "wb") as f :
        f.write(data)

    # extract LUTs directory
    print('Extracting zip file..')
    with zipfile.ZipFile(zip_filepath,"r") as zip_ref:
        zip_ref.extractall(zip_dir)

    # delete zip file
    os.remove(zip_filepath)

    print('Done: LUT files available locally')






# debugging
# iLUTs = handler()
# iLUTs.iLUT_path = '/home/sam'
# iLUTs.get()  # must define one of following: imageCollectionID, satellite_mission, iLUT_path
# print(iLUTs.iLUTs)