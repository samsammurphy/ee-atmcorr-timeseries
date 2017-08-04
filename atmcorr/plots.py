import pandas as pd
from matplotlib import pylab as plt
import matplotlib.dates as mdates

def figure_plotting_space():
    """
    defines the plotting space
    """
  
    fig = plt.figure(figsize=(10,10))
    bar_height = 0.04
    mini_gap = 0.03
    gap = 0.05
    graph_height = 0.24

    axH = fig.add_axes([0.1,gap+3*graph_height+2.5*mini_gap,0.87,bar_height])
    axS = fig.add_axes([0.1,gap+2*graph_height+2*mini_gap,0.87,graph_height])
    axV = fig.add_axes([0.1,gap+graph_height+mini_gap,0.87,graph_height])
    
    return fig, axH, axS, axV

def plot_colorbar(ax,image,ylabel=False):
    """
    display a colorbar (e.g. hue-stretch)
    """
        
    # plot image inside of figure 'axes'
    ax.imshow(image, interpolation='nearest', aspect='auto')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_ylabel(ylabel)

def plot_timeseries(DF, ax, name, startDate, stopDate, ylim=False):
    """
    plots timeseries graphs
    """
  
    # original time series
    ax.plot(DF[name],color='#1f77b4')
    ax.set_ylabel(name)
    ax.set_ylim(ylim)
    ax.set_xlim(pd.datetime.strptime(startDate,'%Y-%m-%d'),\
                pd.datetime.strptime(stopDate,'%Y-%m-%d'))

    # boxcar average
    ax.plot(DF[name].rolling(180).mean(),color='red')

    # make the dates exact
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')

def plotTimeSeries(DF, hue_stretch, startDate, stopDate):

    fig, axH, axS, axV = figure_plotting_space()
    plot_colorbar(axH,[hue_stretch], ylabel='hue')
    plot_timeseries(DF, axS,'sat', startDate, stopDate, ylim=[0,1])
    plot_timeseries(DF, axV,'val', startDate, stopDate)