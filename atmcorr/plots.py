import os
import pandas as pd
import numpy as np
from matplotlib import pylab as plt
import matplotlib.dates as mdates
import colorsys


class Plot():

  def __init__(self, data, startDate, stopDate):
    
    # user input
    self.data = data
    self.startDate = pd.datetime.strptime(startDate,'%Y-%m-%d')
    self.stopDate = pd.datetime.strptime(stopDate,'%Y-%m-%d')
    
    # daily interpolation of input data
    self.interp = data.resample('D').mean().interpolate().ffill().bfill()

  def hue(self, ylim=False, outpath=False):
      """
      plot hue sticks through time
      """

      # data
      df = self.data
      DF = self.interp

      # plot space
      fig, ax = plt.subplots(figsize=(10,4))
      ax.set_ylim(ylim)
      ax.set_xlim(self.startDate,self.stopDate)
      ax.set_ylabel('hue')

      # plot sticks
      for i, date in enumerate(df.index):
        hue = df['hue'][i] 
        if not np.isnan(hue):
          pure_hue = colorsys.hsv_to_rgb(hue,1,1)
          plt.axvline(x=date, color=pure_hue, linewidth=2.5)

      # time line
      linecolor = 'black'##1f77b4'
      ax.plot(DF['hue'],color=linecolor) # interpolated line
      ax.plot(df['hue'],'o',color=linecolor)# original data
      
      # make the dates exact
      ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
      
      fig.show()
      # save to file?
      if outpath:
        fig.savefig(outpath)

  def graph(self, varName, outpath=False):
      """
      plot simple timeseries graph
      """

      # data
      df = self.data
      DF = self.interp

      fig, ax = plt.subplots(figsize=(10,4))

      # plot interpolated
      ax.plot(DF[varName],color='#1f77b4')
      ax.set_ylabel(varName)
      ax.set_xlim(self.startDate,self.stopDate)
      
      # plot original 
      ax.plot(df[varName],'o',color='#1f77b4')

      # make the dates exact
      ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')

      # save to file?
      if outpath:
        fig.savefig(outpath)