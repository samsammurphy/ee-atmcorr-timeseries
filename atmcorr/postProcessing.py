import pandas as pd
import colorsys

def hsv(DF):
    """
    Hue-staturation-value
    """
    rgb = list(zip(DF['red'], DF['green'], DF['blue']))
    DF['hue'] = [colorsys.rgb_to_hsv(x[0], x[1], x[2])[0] for x in rgb]
    DF['sat'] = [colorsys.rgb_to_hsv(x[0], x[1], x[2])[1] for x in rgb]
    DF['val'] = [colorsys.rgb_to_hsv(x[0], x[1], x[2])[2] for x in rgb]
    return DF
  

def postProcessing(allTimeSeries, startDate, stopDate):
    
    # create a dataframe
    df = pd.DataFrame.from_dict(allTimeSeries)

    # timestamp as index
    df.index = [pd.datetime.utcfromtimestamp(t) for t in allTimeSeries['timeStamp']]
    df = df.drop('timeStamp', axis=1)

    # resample to daily
    daily = df.resample('D').mean()

    # fill in NaNs
    interpolated = daily.interpolate().ffill().bfill()

    # clip time series
    DF = interpolated.truncate(before=startDate, after=stopDate)

    # lets add hue-saturation-value color space
    DF = hsv(DF)

    return DF