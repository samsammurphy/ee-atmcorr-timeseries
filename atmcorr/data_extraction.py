"""
Data extraction functions

1) getInfo
2) export

"""

import os
import ee
import pandas as pd
import time
import json

def data_from_getInfo(requests):
    """
    Extracts data from Earth Engine using getInfo()
    
    pro: less work for humans
    con: computational timeouts might occur
    """
    
    print('Requesting data locally')

    dataList = []

    for mission in requests.keys():
        print(mission+'..')
        localData = requests[mission].getInfo()
        dataList.append(localData['features'])
        
    # flatten separate mission lists into a single list
    dataList = [item for sublist in dataList for item in sublist]
    
    # convert to pandas dataframe
    df = dataFrame_from_list(dataList)  
    
    return df
    
def data_export_task(requests, target):
    """
    Creates a data export task
    
    pro: computational timeouts unlikely
    con: more work for humans
    """
       
    requestList = []
    for mission in requests.keys():
        requestList.append(requests[mission])
    
    # flatten separate missions into a single collection
    data = ee.FeatureCollection(requestList).flatten() 
    
    # export task
    task = ee.batch.Export.table.toDrive(
        collection = data,\
        description = 'timeseries_export_from_notebook',\
        folder = '',\
        fileNamePrefix = target)

    return task

 
def task_manager(task, target, e):
  """
  checks progress of earth engine export task
  """

  print('triggering exception:',e)
  
  print("\nExporting to Google Drive..")
  task.start()

  # output directory
  basepath = os.path.dirname(os.path.dirname(__file__))
  csvdir = os.path.join(basepath,'files','csv')
  if not os.path.exists(csvdir):
    os.makedirs(csvdir)
  
  # check for completion
  while task.status()['state'] == 'RUNNING':
    time.sleep(1)
  if task.status()['state'] == 'READY':
    print('success')
    print("\nIMPORTANT! Please download '{}.csv' to:".format(target))  # TODO could use google drive API for this (i.e. avoid user download step)
    print(csvdir)

  # check user has downloaded results
  response = input('Is {}.csv in above directory? (y/n)'.format(target))
  if response[0].lower() == 'y':
    print('\ngreat!\n')
    csvpath = os.path.join(csvdir, target+'.csv')
    if not os.path.isfile(csvpath):
      print('..hmm, did not find .csv file at:\n'+csvpath)
      return None
    else:
      return dataFrame_from_csv(csvpath) 
  else:
    print('CRITICAL: It must be there for the following code to work!')

def dataFrame_from_list(dataList):
  
  # data is stored as feature properties
  properties = [d['properties'] for d in dataList]
  
  # radiance = (cloud-free) average from within geometry
  radiance = pd.DataFrame([p['mean_averages'] for p in properties])
  
  # atmospheric correction inputs
  atmcorr_inputs = pd.DataFrame([p['atmcorr_inputs'] for p in properties])

  # everything else is metadata
  metadata = pd.DataFrame(properties).drop(['atmcorr_inputs','mean_averages'], axis=1)

  # put it all together
  df = pd.concat([metadata, radiance, atmcorr_inputs], axis=1)

  # time index
  df.index = [pd.datetime.utcfromtimestamp(x) for x in df['timeStamp']]
  df = df.drop('timeStamp',axis=1)

  return df

def dataFrame_from_csv(csvpath):
  
  # read csv file
  df = pd.read_csv(csvpath)

  # parse dictionary columns
  radiance = pd.DataFrame([string_to_dic(s) for s in df.pop('mean_averages')])
  atmcorr_inputs = pd.DataFrame([string_to_dic(s) for s in df.pop('atmcorr_inputs')])

  # remove special earth engine variables
  metadata = df.drop(['.geo', 'system:index'], axis=1)
  
  # put it all together
  df = pd.concat([metadata, radiance, atmcorr_inputs], axis=1)

  # time index
  df.index = [pd.datetime.utcfromtimestamp(x) for x in df['timeStamp']]
  df = df.drop('timeStamp',axis=1)

  return df

def string_to_dic(s):
    
    # remove {}
    s = s[1:-1]
    
    # split into list    
    s = s.split(', ')
    
    # create dictionary
    d = {}
    for keyvalue in s:
        kv = keyvalue.split('=')
        d[kv[0]] = kv[1]
    
    return d