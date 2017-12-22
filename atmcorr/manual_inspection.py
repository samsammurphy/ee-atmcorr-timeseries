"""
Collection of routines to help with visually inspection of images
"""

import os
import glob
import pandas as pd

def add_clean_column(df, clean_dir):
  
  def numeric_boolean(x):
    if x:
      return 1
    else:
      return 0
  
  if os.path.exists(clean_dir):
    
    all_IDs = list(df['imageID'])

    clean_paths = sorted(glob.glob(os.path.join(clean_dir, '*.tif')))
    clean_filenames = [os.path.basename(x).split('.')[0] for x in clean_paths]
    clean_IDs = ['_'.join(x.split('_')[2:]) for x in clean_filenames]

    clean_flag = [numeric_boolean(str(x) in clean_IDs) for x in all_IDs]

    df['clean'] = pd.Series(clean_flag, index=df.index)

    return df
  
  else:
    print('directory does not exist:\n'+clean_dir)
    return df