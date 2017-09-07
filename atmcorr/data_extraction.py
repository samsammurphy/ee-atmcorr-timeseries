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

from ee_requests import data_request

class Excel:

  def dir():
    
      base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      excel_dir = os.path.join(base_dir,'files','excel')
      if not os.path.exists(excel_dir):
          os.makedirs(excel_dir)
      return excel_dir
    
  def save(df, target):
      
      df = df.sort_index()# chronological

      df = Excel.nicely_ordered_columns(df)
      
      df.to_excel(os.path.join(Excel.dir(), target+'.xlsx'))

      return df

  def load(target):
    
      file_path = os.path.join(Excel.dir(),target+'.xlsx')

      if os.path.isfile(file_path):
        print('Loading from excel file')
        df = pd.read_excel(file_path)
        return df

  def nicely_ordered_columns(df):
    
      cols = df.columns.tolist()
      
      vswir = [x for x in cols if x[0] == 'B']
      vswir.sort(key=Excel.natural_keys)

      notVSWIR = [x for x in cols if x[0] not in ['B']]

      metadata = notVSWIR[0:2]
      theRest = notVSWIR[2:]

      newcols = metadata + vswir + theRest

      return df[newcols]

  def natural_keys(text):
      '''
      sort in human order
      http://nedbatchelder.com/blog/200712/human_sorting.html
      '''
      def atoi(text):
          return int(text) if text.isdigit() else text

      return [ atoi(c) for c in re.split('(\d+)', text) ]

class Csv:
  
  def dir():
    
      basepath = os.path.dirname(os.path.dirname(__file__))
      csv_dir = os.path.join(basepath,'files','csv')
      if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
      return csv_dir
  
  def string_to_dic(s):

      s = s[1:-1]# remove {}      
      s = s.split(', ')# split to list    

      d = {}
      for keyvalue in s:
          kv = keyvalue.split('=')
          d[kv[0]] = kv[1]

      return d

  def BT_formater(BT_dics):
      """
      Brightness temperature formating

      (i.e. there can be 1 or 2 thermal infrared bands)
      """
      
      BT1 = [x[list(x.keys())[0]] if x[list(x.keys())[0]] != 'null' else None for x in BT_dics]
      BT2 = [x[list(x.keys())[1]] if len(list(x.keys())) == 2 else None for x in BT_dics]

      items = [('tir1', BT1),('tir2', BT2)]
      
      BT = pd.DataFrame.from_items(items)  

      return BT
  
  def to_dataFrame(csvpath):
    
      df = pd.read_csv(csvpath)
      
      radiance = pd.DataFrame([Csv.string_to_dic(s) for s in df.pop('mean_radiance')])
      atmcorr_inputs = pd.DataFrame([Csv.string_to_dic(s) for s in df.pop('atmcorr_inputs')])
      
      BT_dics = [Csv.string_to_dic(s) for s in df.pop('brightness_temperature')]
      BT = Csv.BT_formater(BT_dics)
    
      # remove special earth engine variables
      metadata = df.drop(['.geo', 'system:index'], axis=1)
      
      df = pd.concat([metadata, radiance, BT, atmcorr_inputs], axis=1)

      # time index
      df.index = [pd.datetime.utcfromtimestamp(x) for x in df['timeStamp']]
      df = df.drop('timeStamp',axis=1)

      # cast radiance to float and cast 'null' to NaN
      bands = [x for x in df.columns.tolist() if x[0] == 'B']
      df[bands] = df[bands].apply(pd.to_numeric, errors='coerce')
      
      # cast remaining number columns (ignore strings and datetime)
      df = df.apply(pd.to_numeric, errors='ignore')

      return df
      

class GetInfo:
  
  def extraction(requests):
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
          
      # flatten into single list
      dataList = [item for sublist in dataLists for item in sublist]
      
      # convert to pandas dataframe
      df = GetInfo.dataFrame_from_list(dataList)  
      
      return df
  
  def dataFrame_from_list(dataList):
    
      # data is stored as feature properties
      properties = [d['properties'] for d in dataList]
      
      radiance = pd.DataFrame([p['mean_radiance'] for p in properties])
      
      atmcorr_inputs = pd.DataFrame([p['atmcorr_inputs'] for p in properties])

      BTemperature = Csv.BT_formater([p['brightness_temperature'] for p in properties])

      metadata = pd.DataFrame(properties).drop(['atmcorr_inputs',\
                                                'mean_radiance',\
                                                'brightness_temperature'\
                                                ], axis=1)

      df = pd.concat([metadata, radiance, BTemperature, atmcorr_inputs], axis=1)

      df.index = [pd.datetime.utcfromtimestamp(x) for x in df['timeStamp']]
      df = df.drop('timeStamp',axis=1)

      return df

class GoogleDrive:
    
  def export(requests, target):
      """
      Creates a data export task
      
      pro: computational timeouts unlikely
      con: more work for humans
      """
        
      requestList = []
      for mission in requests.keys():
          requestList.append(requests[mission])
      
      # flatten into a single collection
      data = ee.FeatureCollection(requestList).flatten() 
      
      task = ee.batch.Export.table.toDrive(
          collection = data,\
          description = target+'_timeseries_export',\
          folder = '',\
          fileNamePrefix = target)

      df = GoogleDrive.task_manager(task, target)

      return df

  def task_manager(task, target):
      """
      checks progress of earth engine export task
      """
      
      print("\nExporting to Google Drive..")
      task.start()
      
      while task.status()['state'] in ['RUNNING','READY']:
        time.sleep(1)
      if task.status()['state'] == 'COMPLETED':
        print("Task COMPLETED")
        print("\nIMPORTANT! Please download '{}.csv' to:".format(target))  # TODO could use google drive API for this and avoid user download
        print(Csv.dir())
      else:
        print(task.status())
      
      # data requires user to move csv file
      data = GoogleDrive.download_dialog(target)

      return data

  def download_dialog(target):

      response = input('Is {}.csv in above directory? (y/n)'.format(target))
      if response[0].lower() == 'y':
        print('\ngreat!\n')
        csvpath = os.path.join(Csv.dir(), target+'.csv')
        if not os.path.isfile(csvpath):
          print('..hmm, did not find .csv file at:\n'+csvpath)
          return None
        else:
          return Csv.to_dataFrame(csvpath) 
      else:
        print('CRITICAL: It must be there for the following code to work!')

class Extract:
    
  def using_specific_method(target, requests, method):
      """
      Force use of single method ONLY
      """
      
      if method.lower() == 'excel':
        try:
          return Excel.load(target)
        except:
          return

      if method.lower() == 'getinfo':
        try:
          return GetInfo.extraction(requests)
        except Exception as e:
          print(e)
          return
      
      if method.lower() == 'googledrive':
        try:
          return GoogleDrive.export(requests, target)
        except:
          return
      
      print('method not recognized: '+method)
      print("accepted methods = ['excel', 'getinfo', 'googledrive']")
      return
    
  def trying_each_method(target, requests):
      """
      default is to try all three methods in this order
      1) load from excel
      2) getinfo
      3) export to google drive
      """

      data = Excel.load(target)

      if data is None:
          try:
              return GetInfo.extraction(requests)
          except Exception as e:
              try:
                  print(e)
                  return GoogleDrive.export(requests, target)
              except:
                  pass

  def timeseries(target, geom, startDate, stopDate, missions, method=False):
      """
      Extracts data from Earth Engine. 

      First looks for a local excel file, then tries getinfo
      then tries exporting to google drive.

      If specific method is set, will try ONLY that method
      """
      
      # earth engine data request
      requests = {}
      for mission in missions:
          requests[mission] = data_request(geom, startDate, stopDate, mission)
        
      if method:
        data = Extract.using_specific_method(target, requests, method)
      else:
        data = Extract.trying_each_method(target, requests)
      
      if data is not None:
        return Excel.save(data, target)