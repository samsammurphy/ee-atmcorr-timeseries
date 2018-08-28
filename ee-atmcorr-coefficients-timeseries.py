#!/usr/bin/env python3
# Derive atmospheric correction coefficients for multiple images and optionally export corrected images.
# Created on Mon Aug 6
# @authors: Aman Verma, Preeti Rao

# standard modules
import ee
import datetime
import math
import pickle
ee.Initialize()
# package modules
from atmcorr.atmospheric import Atmospheric
from atmcorr.timeSeries import timeSeries


# AOI and type
target = 'forest'
geom = ee.Geometry.Rectangle(85.5268682942167402, 25.6240533612814261,
                             85.7263954375090407, 25.8241594034421382)
# satellite missions, 
MISSIONS = ['Sentinel2']
# Change this to location of iLUTs
DIRPATH = './files/iLUTs/S2A_MSI/Continental/view_zenith_0/'
# start and end of time series
START_DATE = '2016-11-19'  # YYYY-MM-DD
STOP_DATE = '2017-02-17'  # YYYY-MM-DD
NO_OF_BANDS = 13
# the following creates interpolated lookup tables.
_ = timeSeries(target, geom, START_DATE, STOP_DATE, MISSIONS)

SRTM = ee.Image('CGIAR/SRTM90_V4')  # Shuttle Radar Topography mission covers *most* of the Earth
altitude = SRTM.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom.centroid()).get('elevation').getInfo()
KM = altitude/1000  # i.e. Py6S uses units of kilometers

# The Sentinel-2 image collection
S2 = ee.ImageCollection('COPERNICUS/S2').filterBounds(geom)\
       .filterDate(START_DATE, STOP_DATE).sort('system:time_start')
S2List = S2.toList(S2.size()) # must loop through lists

NO_OF_IMAGES = S2.size().getInfo()  # no. of images in the collection


def atm_corr_image(imageInfo: dict) -> dict:
    """Retrieves atmospheric params from image.

    imageInfo is a dictionary created from an ee.Image object
    """
    atmParams = {}
    # Python uses seconds, EE uses milliseconds:
    scene_date = datetime.datetime.utcfromtimestamp(imageInfo['system:time_start']/1000)
    dt1 = ee.Date(str(scene_date).rsplit(sep=' ')[0])

    atmParams['doy'] = scene_date.timetuple().tm_yday
    atmParams['solar_z'] = imageInfo['MEAN_SOLAR_ZENITH_ANGLE']
    atmParams['h2o'] = Atmospheric.water(geom, dt1).getInfo()
    atmParams['o3'] = Atmospheric.ozone(geom, dt1).getInfo()
    atmParams['aot'] = Atmospheric.aerosol(geom, dt1).getInfo()

    return atmParams


def get_corr_coef(imageInfo: dict, atmParams: dict) -> list:
    """Gets correction coefficients for each band in the image.

    Uses DIRPATH global variable
    Uses NO_OF_BANDS global variable
    Uses KM global variable
    Returns list of 2-length lists
    """
    corr_coefs = []
    # string list with padding of 2
    bandNos = [str(i).zfill(2) for i in range(1, NO_OF_BANDS + 1)]
    for band in bandNos:
        filepath = DIRPATH + 'S2A_MSI_' + band + '.ilut'
        with open(filepath, 'rb') as ilut_file:
            iluTable = pickle.load(ilut_file)
        a, b = iluTable(atmParams['solar_z'], atmParams['h2o'], atmParams['o3'], atmParams['aot'], KM)
        elliptical_orbit_correction = 0.03275104*math.cos(atmParams['doy']/59.66638337) + 0.96804905
        a *= elliptical_orbit_correction
        b *= elliptical_orbit_correction
        corr_coefs.append([a, b])
    return corr_coefs


def toa_to_rad_multiplier(bandname: str, imageInfo: dict, atmParams: dict) -> float:
    """Returns a multiplier for converting TOA reflectance to radiance

    bandname is a string like 'B1'
    """
    ESUN = imageInfo['SOLAR_IRRADIANCE_'+bandname]
    # solar exoatmospheric spectral irradiance
    solar_angle_correction = math.cos(math.radians(atmParams['solar_z']))
    # Earth-Sun distance (from day of year)
    d = 1 - 0.01672 * math.cos(0.9856 * (atmParams['doy']-4))
    # http://physics.stackexchange.com/questions/177949/earth-sun-distance-on-a-given-day-of-the-year
    # conversion factor
    multiplier = ESUN*solar_angle_correction/(math.pi*d**2)
    # at-sensor radiance

    return multiplier


def atm_corr_band(image, imageInfo: dict, atmParams: dict):
    """Atmospherically correct image

    Converts toa reflectance to radiance.
    Applies correction coefficients to get surface reflectance
    Returns ee.Image object
    """
    oldImage = ee.Image(image).divide(10000)
    newImage = ee.Image()
    cor_coeff_list = get_corr_coef(imageInfo, atmParams)
    bandnames = oldImage.bandNames().getInfo()
    for ii in range(NO_OF_BANDS):
        img2RadMultiplier = toa_to_rad_multiplier(bandnames[ii], imageInfo, atmParams)
        imgRad = oldImage.select(bandnames[ii]).multiply(img2RadMultiplier)
        constImageA = ee.Image.constant(cor_coeff_list[ii][0])
        constImageB = ee.Image.constant(cor_coeff_list[ii][1])
        surRef = imgRad.subtract(constImageA).divide(constImageB)
        newImage = newImage.addBands(surRef)

    # unpack a list of the band indexes:
    return newImage.select(*list(range(NO_OF_BANDS)))


S3 = S2List
SrList = ee.List([0]) # Can't init empty list so need a garbage element
export_list = []
coeff_list = []
for i in range(NO_OF_IMAGES):
    iInfo = S3.get(i).getInfo()
    iInfoProps = iInfo['properties']
    atmVars = atm_corr_image(iInfoProps)
    corrCoeffs = get_corr_coef(iInfoProps, atmVars)
    coeff_list.append(corrCoeffs)
    # Uncomment the rest as you please to get an ee.List with the images or even export them to EE.
    # img = atm_corr_band(ee.Image(S2List.get(i)), iInfoProps, atmVars)
    # export = ee.batch.Export.image.toDrive(
    #         image=img,
    #         fileNamePrefix='sen2_' + str(i),
    #         description='py',
    #         scale = 10,
    #         folder = "gee_img",
    #         maxPixels = 1e13
    #         )
    # export_list.append(export)
    # SrList = SrList.add(img)
# SrList = SrList.slice(1) # Need to remove the first element from the list which is garbage
# for task in export_list:
#     task.start()
