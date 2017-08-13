import os
import pandas as pd
import numpy as np
from matplotlib import pylab as plt
import matplotlib.dates as mdates
import colorsys

def targetSpecific(target, varname):
    if varname == 'ylim_pH':
        return None#{'Poas':[-0.5, 2]}[target]

    if varname == 'ylim_sat':
        return [0,0.7]#{'Poas':[0,0.7]}[target]

def load_fieldData(target, startDate, stopDate):
  
  # load from excel
  excel_dir = '/home/sam/github/ee-atmcorr-timeseries/files/field_data/'
  excel_path = os.path.join(excel_dir, target+'_field.xlsx')
  fieldData = pd.read_excel(excel_path)
  
  # date as index
  fieldData.index = fieldData['date']
  
  # load time period
  fieldData = fieldData[startDate:\
                        stopDate]
  
  return fieldData

def saveFig(fig, target, fname):  
  basedir = '/home/sam/Dropbox/IAVCEI/results/autosave/'+target
  if not os.path.exists(basedir):
    os.makedirs(basedir)

  fpath = os.path.join(basedir, fname)
  fig.savefig(fpath)

def plot_history(target, fieldData, startDate, stopDate, save=False):
  
  def eruptive_dates(history, type):
    event = history[type]
    dates = history['date']
    datesOfInterest = []

    for i, e in enumerate(event):
      if e == 1:
        datesOfInterest.append(dates[i])
    return datesOfInterest
    
  def axvlines(ax, dates, **plot_kwargs):
      """
      Draw vertical lines on plot
      :param xs: A scalar, list, or 1D array of horizontal offsets
      :param plot_kwargs: Keyword arguments to be passed to plot
      :return: The plot object corresponding to the lines.

      https://stackoverflow.com/questions/24988448/how-to-draw-vertical-lines-on-a-given-plot-in-matplotlib
      """
      xs = np.array((dates, ) if np.isscalar(dates) else dates, copy=False)
      lims = ax.get_ylim()
      x_points = np.repeat(xs[:, None], repeats=3, axis=1).flatten()
      y_points = np.repeat(np.array(lims + (np.nan, ))[None, :], repeats=len(xs), axis=0).flatten()
      ax.plot(x_points, y_points, scaley = False, **plot_kwargs)
      return ax

  def plot_eruptive_history(ax, fieldData):
    
    unrest = eruptive_dates(fieldData, 'unrest')
    eruption = eruptive_dates(fieldData, 'eruption')

    ax = axvlines(ax, unrest, color='gray')
    ax = axvlines(ax, eruption, color='red')
    
    return ax

  fig, ax = plt.subplots(figsize=(10,2))
  ax = plot_eruptive_history(ax, fieldData)
  ax.set_ylabel('history') 
  ax.yaxis.set_major_formatter(plt.NullFormatter())
  ax.set_xlim(startDate,stopDate)
  
  if save:
    saveFig(fig, target, fname='history.png')

def plot_acid(target, fieldData, startDate, stopDate, history=True, save=False):

    fig, ax = plt.subplots(figsize=(10,4))
   
    # Cl
    ax.plot(fieldData['date'], np.array(fieldData['Cl'])/1000, color='orange', label='Cl')
    ax.set_xlim(startDate,stopDate)
    ax.set_ylabel('Cl') 
    ax.set_xlim(startDate,stopDate)
    ax.tick_params('y', colors='orange', labelsize=12)

    # pH
    ax2 = ax.twinx()
    ax2.plot(fieldData['date'], fieldData['pH'], color='#1f77b4', label='pH')
    ax2.set_ylabel('pH')
    ax2.set_ylim(targetSpecific(target, 'ylim_pH'))
    ax2.set_xlim(startDate,stopDate)
    ax2.tick_params('y', colors='#1f77b4', labelsize=12)

    if save:
      saveFig(fig, target, fname='acid.png')

def plot_color(target, data, name, startDate, stopDate,fieldData, history=True, save=False):
    """
    plot lake color through time
    """

    # data frames
    df = data[0]# original
    DF = data[1]# interpolated

    fig, ax = plt.subplots(figsize=(10,4))

    # interpolated time series
    ax.plot(DF[name],color='#1f77b4')
    ax.set_ylabel(name)
    ax.set_xlim(startDate,stopDate)
    
    # hack
    if name == 'sat':
      ax.set_ylim(targetSpecific(target, 'ylim_sat'))

    # original data
    ax.plot(df[name],'o',color='#1f77b4')

    # make the dates exact
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')

    if save:
      saveFig(fig, target, fname=name+'.png')

def plot_hueSticks(target, data, startDate, stopDate, ylim=False, save=False):
    """
    plot hue sticks through time
    """
    
    # data frames
    df = data[0]# original
    
    # interpolate
    resampled = df.resample('M').mean()
    DF = resampled.interpolate().ffill().bfill()
    
    # plot space
    fig, ax = plt.subplots(figsize=(10,4))
    ax.set_ylim(ylim)
    ax.set_xlim(startDate,stopDate)
    ax.set_ylabel('hue')

    # plot sticks
    for i, date in enumerate(DF.index):
      hue = DF['hue'][i] 
      if not np.isnan(hue):
        pure_hue = colorsys.hsv_to_rgb(hue,1,1)
        plt.axvline(x=date, color=pure_hue, linewidth=2)

    
    # time line
    linecolor = 'black'##1f77b4'
    ax.plot(DF['hue'],color=linecolor) # interpolated line
    ax.plot(df['hue'],'o',color=linecolor)# original data
    
    # make the dates exact
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')

    if save:
      saveFig(fig, target, fname='hue.png')


def plot_other(target, fieldData, startDate, stopDate, ylim=False, history=True, save=False):
    
    fig, ax = plt.subplots(figsize=(10,4))

    def normPlot(ax, fieldData, name, color= False):
      arr = np.array(fieldData[name])
      ax.plot(fieldData['date'], arr/np.nanmax(arr), color=color, label=name)
      
    normPlot(ax, fieldData, 'SO4', color= '#17becf')
    normPlot(ax, fieldData, 'Fe', color= '#d62728')
    normPlot(ax, fieldData, 'Mg', color= '#9467bd')
    normPlot(ax, fieldData, 'Ca', color= '#ff7f0e')
    normPlot(ax, fieldData, 'Na', color= '#e377c2')
    normPlot(ax, fieldData, 'K',  color= '#2ca02c')
    normPlot(ax, fieldData, 'Al', color= '#7f7f7f')
    
    ax.set_ylabel('normalized chemistry')
    ax.set_ylim([0,1])
    ax.set_xlim(startDate,stopDate)
    ax.legend()

    if save:
      saveFig(fig, target, fname='other.png')


