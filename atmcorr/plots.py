"""
plots.py
"""

from matplotlib import pylab as plt
import datetime

def visPlot(timeSeries):
  """
  plots visible wavebands
  """

  vizBandSwitch = {
    'Sentinel2':('B2','B3','B4'),
    'Landsat8':('B2','B3','B4'),
    'Landsat7':('B1','B2','B3'),
    'Landsat5':('B1','B2','B3'),
    'Landsat4':('B1','B2','B3')

  }

  vizBands = vizBandSwitch[timeSeries['mission']]

  plt.plot(timeSeries['dates'], timeSeries[vizBands[0]], 'blue')
  plt.plot(timeSeries['dates'], timeSeries[vizBands[1]], 'green')
  plt.plot(timeSeries['dates'], timeSeries[vizBands[2]], 'red')
  plt.title('RGB')
  plt.show()

def nirPlot(timeSeries):

  nirSwitch = {
    'Sentinel2':{'bands':['B5','B6','B7','B7'],
                 'colors':['#cbc9e2', '#9e9ac8', '#756bb1', '#54278f'],
                 'labels':['705 nm', '740 nm', '783 nm', '842 nm']},

    'Landsat8':{'bands':['B5'],
                 'colors':['#cbc9e2'],
                 'labels':['865 nm']},

    'Landsat7':{'bands':['B4'],
                 'colors':['#cbc9e2'],
                 'labels':['830 nm']},

    'Landsat5':{'bands':['B4'],
                 'colors':['#cbc9e2'],
                 'labels':['830 nm']},

    'Landsat4':{'bands':['B4'],
                 'colors':['#cbc9e2'],
                 'labels':['830 nm']}

  }

  config = nirSwitch[timeSeries['mission']]

  for i, band in enumerate(config['bands']):
    plt.plot(timeSeries['dates'], timeSeries[band], config['colors'][i], label=config['labels'][i])
  
  plt.title('Near Infrared')
  plt.legend()
  plt.show()

def swirPlot(timeSeries):

  swirSwitch = {
    'Sentinel2':{'bands':['B11','B12'],
                 'colors':['#993404', '#fe9929'],
                 'labels':['1610 nm', '2190 nm']},

    'Landsat8':{'bands':['B6','B7'],
                 'colors':['#993404', '#fe9929'],
                 'labels':['1610 nm', '2200 nm']},

    'Landsat7':{'bands':['B5','B7'],
                 'colors':['#993404', '#fe9929'],
                 'labels':['1650 nm', '2270 nm']},

    'Landsat5':{'bands':['B5','B7'],
                 'colors':['#993404', '#fe9929'],
                 'labels':['1650 nm', '2270 nm']},

    'Landsat4':{'bands':['B5','B7'],
                 'colors':['#993404', '#fe9929'],
                 'labels':['1650 nm', '2270 nm']}

  }

  config = swirSwitch[timeSeries['mission']]

  for i, band in enumerate(config['bands']):
    plt.plot(timeSeries['dates'], timeSeries[band], config['colors'][i], label=config['labels'][i])
  
  plt.title('Short-wave Infrared')
  plt.legend()
  plt.show()

def atmPlot(timeSeries):

  atmSwitch = {
    'Sentinel2':{'bands':['B1','B9','B10'],
                 'colors':['#c994c7', '#225ea8', '#c7e9b4'],
                 'labels':['aerosol (443 nm)', 'water vapour (940 nm)', 'cirrus (1375 nm)']},

    'Landsat8':{'bands':['B1','B9'],
                 'colors':['#c994c7','#c7e9b4'],
                 'labels':['aerosol (440 nm)', 'cirrus (1370 nm)']},

    'Landsat7':None,

    'Landsat5':None,

    'Landsat4':None

  }

  config = atmSwitch[timeSeries['mission']]

  if not config:
    return None

  for i, band in enumerate(config['bands']):
    plt.plot(timeSeries['dates'], timeSeries[band], config['colors'][i], label=config['labels'][i])
    
  plt.title('Atmospheric')
  plt.legend()
  plt.show()

def plot_timeseries(timeSeries, plotType):
  
  timeSeries['dates'] = [datetime.datetime.utcfromtimestamp(dt) for dt in timeSeries['timeStamp']]
  
  switch = {
    'visible':visPlot,
    'nir':nirPlot,
    'swir':swirPlot,
    'atmospheric':atmPlot
  }
  
  return switch[plotType](timeSeries)






