"""
Batch export/download of 'quicklook' images to/from cloud storage

'quicklook' = an image subset (both spatially and spectrally)
"""

import os
import ee
import sys
import numpy as np
import pandas as pd
from image_viewer import *

try:
  from google.cloud import storage
except:
  print('\nDo you have the Google Cloud Client Library for Python installed?')
  print('\npip install google-cloud')
  sys.exit(1)

def export_rgb(data, region, bucket, targetName=False, maxValue=False):
    """
    Exports surface reflectance RGBs
    """

    response = input('Are you sure you want to export {} images? (y/n)'.format(len(data)))
    if response.lower() in ['n','no','nope']:
      print('export aborted')
      return 
    else:
      print('exporting..')

    if not targetName:
      targetName = 'target'

    if not maxValue:
      maxValue = 0.35
    
    # surface reflectance filter 
    data = data[np.array(pd.notnull(data['blue']))]

    try:
      
      for i in range(len(data)):
        scene = data.iloc[i]
        satellite_fileID = scene['imageID']

        print(satellite_fileID)

        rgb = surface_reflectance_image(scene, ['red','green','blue'])
        img = rgb.visualize(min=0, max=maxValue)
        
        date_time = data.index[i].to_pydatetime().strftime("%Y-%m-%d")      
        fpath = targetName+'/'+targetName+'_'+date_time+'_'+satellite_fileID

        ee.batch.Export.image.toCloudStorage(
            image = img, 
            description = targetName+'_batch_png_export', 
            bucket = bucket , 
            fileNamePrefix = fpath,
            region = region,
            scale=10).start()

      print('done')

    except Exception as e:
      print(e)

def download_rgb(targetName, bucketName, local_dir):
    """
    Downloads quicklook images from cloud storage
    """

    try:
   
      storage_client = storage.Client()
      bucket = storage_client.get_bucket(bucketName)
      blobs = bucket.list_blobs()

      images = [x for x in blobs if os.path.splitext(x.name)[1] == '.tif']
      target_images = [x for x in images if x.name.split('/')[0] == targetName]

      print('{} target images'.format(len(target_images)))

      for img in target_images:
        local_file_name = img.name.split('/')[1]
        local_path = os.path.join(local_dir, local_file_name)
        img.download_to_filename(local_path)
        
        print('Blob {} downloaded to \n{}.'.format(
            img.name,
            local_path))
    
    except Exception as e:
      print(e)
