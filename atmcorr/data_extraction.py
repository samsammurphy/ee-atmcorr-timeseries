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
import re
import glob

def extract_using_getInfo(requests):
    """
    Extracts data from Earth Engine using getInfo()
    
    pro: less work for humans
    con: computational timeouts might occur
    """
    
    print('Requesting data locally')

    dataLists = []

    for mission in requests.keys():
        print(mission+'..')
        localData = requests[mission].getInfo()
        dataLists.append(localData['features'])
        
    # flatten separate mission lists into a single list
    dataList = [item for sublist in dataLists for item in sublist]
    
    # convert to pandas dataframe
    df = dataFrame_from_list(dataList)  
    
    return df

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

def export_to_google_drive(requests, target):
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
        description = target+'_timeseries_export',\
        folder = '',\
        fileNamePrefix = target)

    df = task_manager(task, target)

    return df

def dialog_export_download_check(target, csvdir):

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

def task_manager(task, target):
  """
  checks progress of earth engine export task
  """
  
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
  
  # data requires user to move csv file
  data = dialog_export_download_check(target, csvdir)

  return data

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

  # data type casting
  df = explicit_cast(df)

  return df

def explicit_cast(df):
  
  # radiance to float and cast 'null' to NaN
  bands = [x for x in df.columns.tolist() if x[0] == 'B']
  df[bands] = df[bands].apply(pd.to_numeric, errors='coerce')
  
  # cast remaining number columns (ignore strings and datetime)
  df = df.apply(pd.to_numeric, errors='ignore')

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

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    '''
    def atoi(text):
        return int(text) if text.isdigit() else text

    return [ atoi(c) for c in re.split('(\d+)', text) ]
    
def nicely_ordered_columns(df):
  
  cols = df.columns.tolist()
  
  bands = [x for x in cols if x[0] == 'B']
  bands.sort(key=natural_keys)

  notBands = [x for x in cols if x[0] != 'B']

  metadata = notBands[0:2]
  theRest = notBands[2:]

  newcols = metadata + bands + theRest

  return df[newcols]

def single_method_extraction(target, requests, method):
  """
  Force use of single method ONLY
  """
  
  if method.lower() == 'excel':
    try:
      return load_from_excel(target)
    except:
      return

  if method.lower() == 'getinfo':
    try:
      return extract_using_getInfo(requests)
    except Exception as e:
      print(e)
      return
  
  if method.lower() == 'googledrive':
    try:
      return export_to_google_drive(requests, target)
    except:
      return

  print('method not recognized: '+method)
  print("accepted methods = ['excel', 'getinfo', 'googledrive']")
  return
  
def default_method_extraction(target, requests):
  """
  default is to try all three methods in this order
  1) load from excel
  2) getinfo
  3) export to google drive
  """

  data = load_from_excel(target)

  if data is None:
      try:
          return extract_using_getInfo(requests)
      except Exception as e:
          try:
              print(e)
              return export_to_google_drive(requests, target)
          except:
              pass

def data_extractor(target, requests, method=False):
  """
  Extracts data from Earth Engine. 

  First looks for a local excel file, then tries getinfo
  then tries exporting to google drive.

  If specific method is set, will try ONLY that method
  """
  
  # get data
  if method:
    data = single_method_extraction(target, requests, method)
  else:
    data = default_method_extraction(target, requests)

  if data is not None:

    # chronological_sort
    data = data.sort_index()
    
    # column ordering
    data = nicely_ordered_columns(data)

    # save local copy
    save_to_excel(data, target)

    return data

def save_to_excel(df, target):
    
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_dir = os.path.join(basedir,'files','excel')
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)

    df.to_excel(os.path.join(excel_dir, target+'.xlsx'))

def load_from_excel(target):
  
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(basedir,'files','excel',target+'.xlsx')

    if os.path.isfile(excel_path):
      print('Loading from excel file')
      df = pd.read_excel(excel_path)
      return df