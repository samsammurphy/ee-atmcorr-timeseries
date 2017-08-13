import pandas as pd
import colorsys

def hsv(df):
    """
    Hue-staturation-value
    """
    rgb = list(zip(df['red'], df['green'], df['blue']))
    df['hue'] = [colorsys.rgb_to_hsv(x[0], x[1], x[2])[0] for x in rgb]
    df['sat'] = [colorsys.rgb_to_hsv(x[0], x[1], x[2])[1] for x in rgb]
    df['val'] = [colorsys.rgb_to_hsv(x[0], x[1], x[2])[2] for x in rgb]
    return df
  

def postProcessing(allTimeSeries):
    
    # create a dataframe
    df = pd.DataFrame.from_dict(allTimeSeries)

    # timestamp as index
    df.index = [pd.datetime.utcfromtimestamp(t) for t in allTimeSeries['timeStamp']]
    df = df.drop('timeStamp', axis=1)

    # HSV color space
    df = hsv(df)

    # daily freqeuncy
    daily = df.resample('D').mean()

    # interpolate
    DF = daily.interpolate().ffill().bfill()
    # DF = interpolated.truncate(before=startDate, after=stopDate)

    return (df, DF)