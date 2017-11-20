"""
Collection of routines to help with visually inspection of images
"""

import os
import glob
import pandas as pd

def add_clean_column(df, clean_dir):
  
  def binary_boolean(x):
    if x:
      return 1
    else:
      return 0
  
  if os.path.exists(clean_dir):
    
    all_IDs = list(df['imageID'])

    clean_image_paths = glob.glob(os.path.join(clean_dir, '*.tif'))
    clean_image_fnames = [os.path.basename(x) for x in clean_image_paths]
    clean_IDs = [os.path.splitext(x)[0].split('_')[-1] for x in clean_image_fnames]

    clean_list = [binary_boolean(x in clean_IDs) for x in all_IDs]

    df['clean'] = pd.Series(clean_list, index=df.index)

    return df
  
  else:
    print('directory does not exist:\n'+clean_dir)
    return df