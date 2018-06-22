# QAQC script for weather data
# Written by Christian Dunkerly
# chrisdunkerly@gmail.com
# Last updated 4/14/2018

from __future__ import division

import configparser
import logging
import datetime as dt
import numpy as np
import sys
import math
import refet
import pandas as pd
from qaqc_modules.rs_et_calc import emprso_w_tr
from qaqc_modules.correction import *

from bokeh.plotting import *
from bokeh.layouts import *

logging.basicConfig()
print("\nSystem: Starting QAQC script.")
print(dt.datetime.now())

# Open config file
data_config = configparser.ConfigParser()
data_config.read('config.ini')
print("\nSystem: Reading in .ini file.")
print(dt.datetime.now())

# read in meta variables from config file to open data
file_path = data_config['DEFAULT']['file_path']
missing_data_value = data_config['DATA']['missing_data_value']
lines_of_header = data_config['DEFAULT'].getint('lines_of_header')
lines_of_footer = data_config['DEFAULT'].getint('lines_of_footer')
station_elev = data_config['DEFAULT'].getfloat('station_elev')  # Expected in meters
station_lat = data_config['DEFAULT'].getfloat('station_lat')  # Expected in decimal degrees
log_bool = data_config['MODES'].getboolean('log_mode')

station_text = file_path.split('.')
station_name = station_text[0]

# Create log file that will keep track of corrections
log_file = station_name + "_corrections_log" + ".txt"
logger = open(log_file, 'w')
logger.write('The log file for filename %s has been successfully created at %s. \n' % (station_name,
                                                                                       dt.datetime.now().strftime(
                                                                                           "%Y-%m-%d %H:%M:%S")))
logger.close()

if log_bool:
    print("\nSystem: User has specified using a log file, all output will be written to script_log.txt.")
    # TODO consider removing now that log is a separate thing
    # Open logging file
    log_file = open("script_log.txt", 'w')
    sys.stdout = log_file
else:
    pass

# read in data and trim it of header and footer
raw_data = np.genfromtxt(file_path, dtype='U', delimiter=',', skip_header=lines_of_header,
                         skip_footer=lines_of_footer, autostrip=True)
raw_rows = raw_data.shape[0]
raw_cols = raw_data.shape[1]
print("\nSystem: Raw data successfully read in.")
print(dt.datetime.now())

# go through raw data and replace missing data values with nans
# note that values will not be nan until list is typecast as a float
for i in range(raw_rows):
    for j in range(raw_cols):
        if missing_data_value in raw_data[i, j]:
            raw_data[i, j] = np.nan
        else:
            pass

########################################################################################################################
# Date handling section - @DHS
# Figures out the date format and extracts from string if needed

date_format = data_config['DATA'].getint('date_format')
if date_format == 1:
    # String date
    date_col = data_config['DATA'].getint('date_col')
    date_time_included = data_config['DATA'].getboolean('date_time_included')  # see if HOURS:MINUTES was attached

    if date_col != -1:
        input_date = np.array(raw_data[:, date_col])
    else:
        input_date = np.array([])
    data_date = input_date
    data_length = data_date.shape[0]

    # Extract date information and produce DOY and serial date
    if date_time_included:
        date_format = "%m/%d/%Y %H:%M"
    else:
        date_format = "%m/%d/%Y"

    data_day = []
    data_month = []
    data_year = []

    for i in range(data_length):
        date_info = dt.datetime.strptime(data_date[i], date_format)
        data_day.append(date_info.day)
        data_month.append(date_info.month)
        data_year.append(date_info.year)

    # Convert to np arrays
    data_day = np.array(data_day)
    data_month = np.array(data_month)
    data_year = np.array(data_year)

elif date_format == 2:
    # Date is pre-split into several columns
    month_col = data_config['DATA'].getint('month_col')
    day_col = data_config['DATA'].getint('day_col')
    year_col = data_config['DATA'].getint('year_col')

    data_month = np.array(raw_data[:, month_col].astype('int'))
    data_day = np.array(raw_data[:, day_col].astype('int'))
    data_year = np.array(raw_data[:, year_col].astype('int'))

    data_length = data_month.shape[0]

    # Convert to np arrays
    data_day = np.array(data_day)
    data_month = np.array(data_month)
    data_year = np.array(data_year)
# End of data handling section
########################################################################################################################

########################################################################################################################
# Data extraction section - @DES
# split off different variables into their own lists and type them as float
# first we have to read in the config file variables that tell us which variable is where
# these variables will serve later as booleans (!= -1) for downstream calculation of secondary vars

rs_col = data_config['DATA'].getint('rs_col')
ws_col = data_config['DATA'].getint('ws_col')
tmax_col = data_config['DATA'].getint('tmax_col')
tmin_col = data_config['DATA'].getint('tmin_col')
tavg_col = data_config['DATA'].getint('tavg_col')
tdew_col = data_config['DATA'].getint('tdew_col')
precip_col = data_config['DATA'].getint('precip_col')
vappres_col = data_config['DATA'].getint('vappres_col')
rhmax_col = data_config['DATA'].getint('rhmax_col')
rhmin_col = data_config['DATA'].getint('rhmin_col')
rhavg_col = data_config['DATA'].getint('rhavg_col')
etrs_col = data_config['DATA'].getint('etrs_col')
etos_col = data_config['DATA'].getint('etos_col')

# next we split the data up and type them as float, except for date which stays str
# also requires checking to see which variables are actually provided, setting missing vars to empty arrays

if rs_col != -1:
    input_rs = np.array(raw_data[:, rs_col].astype('float'))
else:
    input_rs = np.array([])
if ws_col != -1:
    input_ws = np.array(raw_data[:, ws_col].astype('float'))
else:
    input_ws = np.array([])
if tmax_col != -1:
    input_tmax = np.array(raw_data[:, tmax_col].astype('float'))
else:
    input_tmax = np.array([])
if tmin_col != -1:
    input_tmin = np.array(raw_data[:, tmin_col].astype('float'))
else:
    input_tmin = np.array([])
if tavg_col != -1:
    input_tavg = np.array(raw_data[:, tavg_col].astype('float'))
else:
    input_tavg = np.array([])
if tdew_col != -1:
    input_tdew = np.array(raw_data[:, tdew_col].astype('float'))
else:
    input_tdew = np.array([])
if precip_col != -1:
    input_precip = np.array(raw_data[:, precip_col].astype('float'))
else:
    input_precip = np.array([])
if vappres_col != -1:
    input_vappres = np.array(raw_data[:, vappres_col].astype('float'))
else:
    input_vappres = np.array([])
if rhmax_col != -1:
    input_rhmax = np.array(raw_data[:, rhmax_col].astype('float'))
else:
    input_rhmax = np.array([])
if rhmin_col != -1:
    input_rhmin = np.array(raw_data[:, rhmin_col].astype('float'))
else:
    input_rhmin = np.array([])
if rhavg_col != -1:
    input_rhavg = np.array(raw_data[:, rhavg_col].astype('float'))
else:
    input_rhavg = np.array([])
if etrs_col != -1:
    input_etrs = np.array(raw_data[:, etrs_col].astype('float'))
else:
    input_etrs = np.array([])
if etos_col != -1:
    input_etos = np.array(raw_data[:, etos_col].astype('float'))
else:
    input_etos = np.array([])

ws_anemometer_height = data_config['DEFAULT'].getfloat('ws_anemometer_height')  # Expected in meters
missing_fill_value = data_config['DATA']['missing_fill_value']
# End of data extraction section
########################################################################################################################

########################################################################################################################
# Unit conversion section - @UCS
# read in flags to determine if units need to be converted or not

rs_lang_flag = data_config['DATA'].getboolean('rs_lang_flag')
rs_mj_flag = data_config['DATA'].getboolean('rs_mj_flag')
rs_kw_hr_flag = data_config['DATA'].getboolean('rs_kw_hr_flag')
ws_mph_flag = data_config['DATA'].getboolean('ws_mph_flag')
tmax_f_flag = data_config['DATA'].getboolean('tmax_f_flag')
tmin_f_flag = data_config['DATA'].getboolean('tmin_f_flag')
tavg_f_flag = data_config['DATA'].getboolean('tavg_f_flag')
tdew_f_flag = data_config['DATA'].getboolean('tdew_f_flag')
vappres_torr_flag = data_config['DATA'].getboolean('vappres_torr_flag')
rhmax_fract_flag = data_config['DATA'].getboolean('rhmax_fraction_flag')
rhmin_fract_flag = data_config['DATA'].getboolean('rhmin_fraction_flag')
rhavg_fract_flag = data_config['DATA'].getboolean('rhavg_fraction_flag')
precip_inch_flag = data_config['DATA'].getboolean('precip_inch_flag')
etrs_inch_flag = data_config['DATA'].getboolean('etrs_inch_flag')
etos_inch_flag = data_config['DATA'].getboolean('etos_inch_flag')

# Now converting data into appropriate units
# after checking to see if given data exists
# Solar Radiation
if input_rs.size != 0:
    if rs_lang_flag == 1:
        data_rs = np.array(input_rs * 0.48458)
    elif rs_mj_flag == 1:
        data_rs = np.array(input_rs * 11.574)  # EQ from https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
    elif rs_kw_hr_flag == 1:
        data_rs = np.array((input_rs * 1000) / 24)  # EQ from rapidtables.com
    else:
        # Data is provided in w/m2
        data_rs = np.array(input_rs)
else:
    data_rs = np.array([])  # Variable is not provided

# Wind speed
if input_ws.size != 0:
    if ws_mph_flag == 1:
        data_ws = np.array(input_ws * 0.44704)
    else:
        # Data is provided in m/s
        data_ws = np.array(input_ws)
else:
    data_ws = np.array([])  # Variable is not provided

# Temp Max
if input_tmax.size != 0:
    if tmax_f_flag == 1:
        data_tmax = np.array(((input_tmax - 32.0) * (5.0 / 9.0)))
    else:
        # Data is provided in C
        data_tmax = np.array(input_tmax)
else:
    data_tmax = np.array([])  # Variable is not provided

# Temp Min
if input_tmin.size != 0:
    if tmin_f_flag == 1:
        data_tmin = np.array(((input_tmin - 32.0) * (5.0 / 9.0)))
    else:
        # Data is provided in C
        data_tmin = np.array(input_tmin)
else:
    data_tmin = np.array([])  # Variable is not provided

# Temp Avg
if input_tavg.size != 0:
    if tavg_f_flag == 1:
        data_tavg = np.array(((input_tavg - 32.0) * (5.0 / 9.0)))
    else:
        # Data is provided in C
        data_tavg = np.array(input_tavg)
else:
    data_tavg = np.array([])  # Variable is not provided

# Temp Dew
if input_tdew.size != 0:
    if tdew_f_flag == 1:
        data_tdew = np.array(((input_tdew - 32.0) * (5.0 / 9.0)))
    else:
        # Data is provided in C
        data_tdew = np.array(input_tdew)
else:
    data_tdew = np.array([])  # Variable is not provided

# Precip
if input_precip.size != 0:
    if precip_inch_flag == 1:
        data_precip = np.array(input_precip * 25.4)
    else:
        # Data is provided in mm
        data_precip = np.array(input_precip)
else:
    data_precip = np.array([])  # Variable is not provided

# Vapor Pressure
if input_vappres.size != 0:
    if vappres_torr_flag == 1:
        data_vappres = np.array(input_vappres * 0.133322)
    else:
        # Data is provided in kPa
        data_vappres = np.array(input_vappres)
else:
    data_vappres = np.array([])  # Variable is not provided

# RHMax
if input_rhmax.size != 0:
    if rhmax_fract_flag == 1:
        data_rhmax = np.array(input_rhmax * 100.0)
    else:
        # Data is provided as a %
        data_rhmax = np.array(input_rhmax)
else:
    data_rhmax = np.array([])  # Variable is not provided

# RHMin
if input_rhmin.size != 0:
    if rhmin_fract_flag == 1:
        data_rhmin = np.array(input_rhmin * 100.0)
    else:
        # Data is provided as a %
        data_rhmin = np.array(input_rhmin)
else:
    data_rhmin = np.array([])  # Variable is not provided

# RHAvg
if input_rhavg.size != 0:
    if rhavg_fract_flag == 1:
        data_rhavg = np.array(input_rhavg * 100.0)
    else:
        # Data is provided as a %
        data_rhavg = np.array(input_rhavg)
else:
    data_rhavg = np.array([])  # Variable is not provided
# Etrs
if input_etrs.size != 0:
    if etrs_inch_flag == 1:
        data_etrs = np.array(input_etrs * 25.4)
    else:
        # Data is provided in mm
        data_etrs = np.array(input_etrs)
else:
    data_etrs = np.array([])  # Variable is not provided

# Etos
if input_etos.size != 0:
    if etos_inch_flag == 1:
        data_etos = np.array(input_etos * 25.4)
    else:
        # Data is provided in mm
        data_etos = np.array(input_etos)
else:
    data_etos = np.array([])  # Variable is not provided

# End of unit conversion section
########################################################################################################################

########################################################################################################################
# Preliminary data corrections - @PDC
# Apply logical limits to data and throw out bad data points
for i in range(data_length):
    # rs
    if data_rs.size != 0:
        if data_rs[i] <= 5 or data_rs[i] >= 700:  # Todo see if this is a valid limit
            data_rs[i] = np.nan
        else:
            pass
    else:
        pass
    # ws
    if data_ws.size != 0:
        if data_ws[i] <= 0 or data_ws[i] >= 70:  # 70 m/s is a category 5 hurricane, probably a safe cutoff
            data_ws[i] = np.nan
        else:
            pass
    else:
        pass
    # tmax
    if data_tmax.size != 0:
        if data_tmax[i] <= -50 or data_tmax[i] >= 60:  # 60 C is 140 F so probably a safe cutoff
            data_tmax[i] = np.nan
        else:
            pass
    else:
        pass
    # tmin
    if data_tmin.size != 0:
        if data_tmin[i] <= -50 or data_tmin[i] >= 60:
            data_tmin[i] = np.nan
        else:
            pass
    else:
        pass
    # tavg
    if data_tavg.size != 0:
        if data_tavg[i] <= -50 or data_tavg[i] >= 60:
            data_tavg[i] = np.nan
        else:
            pass
    else:
        pass
    # tdew
    if data_tdew.size != 0:
        if data_tdew[i] <= -50 or data_tdew[i] >= 60:
            data_tdew[i] = np.nan
        else:
            pass
    else:
        pass
    # precip
    if data_precip.size != 0:
        if data_precip[i] < 0 or data_precip[i] > 600:  # 600 mm is ~2 feet of rain in a day, probably a safe cutoff
            data_precip[i] = np.nan
        else:
            pass
    else:
        pass
    # rhmax
    if data_rhmax.size != 0:
        if data_rhmax[i] > 100 or data_rhmax[i] < 2:
            data_rhmax[i] = np.nan
        else:
            pass
    else:
        pass
    # rhmin
    if data_rhmin.size != 0:
        if data_rhmin[i] > 100 or data_rhmin[i] < 2:
            data_rhmin[i] = np.nan
        else:
            pass
    else:
        pass
    # rhavg
    if data_rhavg.size != 0:
        if data_rhavg[i] > 100 or data_rhavg[i] < 2:
            data_rhavg[i] = np.nan
        else:
            pass
    else:
        pass
    # vapor pressure
    if data_vappres.size != 0:
        if data_vappres[i] <= 0 or data_vappres[i] >= 8:  # TODO check to see if this limit is okay
            data_vappres[i] = np.nan
        else:
            pass
    else:
        pass
    # etrs
    if data_etrs.size != 0:
        if data_etrs[i] <= 0:
            data_etrs[i] = np.nan
        else:
            pass
    else:
        pass
    # etos
    if data_etos.size != 0:
        if data_etos[i] <= 0:
            data_etos[i] = np.nan
        else:
            pass
    else:
        pass

# End of preliminary data conversion
########################################################################################################################

########################################################################################################################
# Dataframe Resampling Section - @DRS
# In this section we convert the raw data into a pandas dataframe to make use
# their resampling function to fill in missing timeseries data before going back to numpy arrays
# We also fill in missing variables with NaN values because dataframes require all columns to be same length

###########
# Fill in any unprovided variables so subsequent dataframe has variables of all the same length
# Solar
if input_rs.size == 0:
    data_rs = np.zeros(data_length)
    data_rs[:] = np.nan
else:
    pass
# Wind
if input_ws.size == 0:
    data_ws = np.zeros(data_length)
    data_ws[:] = np.nan
else:
    pass
# Precip
if input_precip.size == 0:
    data_precip = np.zeros(data_length)
    data_precip[:] = np.nan
else:
    pass
# Temp
if input_tmax.size == 0:
    data_tmax = np.zeros(data_length)
    data_tmax[:] = np.nan
else:
    pass
if input_tmin.size == 0:
    data_tmin = np.zeros(data_length)
    data_tmin[:] = np.nan
else:
    pass
if input_tavg.size == 0:
    data_tavg = np.zeros(data_length)
    data_tavg[:] = np.nan
else:
    pass
if input_tdew.size == 0:
    data_tdew = np.zeros(data_length)
    data_tdew[:] = np.nan
else:
    pass
# Vapor Pressure
if input_vappres.size == 0:
    data_vappres = np.zeros(data_length)
    data_vappres[:] = np.nan
else:
    pass
# Relative Humidity
if input_rhmax.size == 0:
    data_rhmax = np.zeros(data_length)
    data_rhmax[:] = np.nan
else:
    pass
if input_rhmin.size == 0:
    data_rhmin = np.zeros(data_length)
    data_rhmin[:] = np.nan
else:
    pass
if input_rhavg.size == 0:
    data_rhavg = np.zeros(data_length)
    data_rhavg[:] = np.nan
else:
    pass
# Station ET
if input_etos.size == 0:
    data_etos = np.zeros(data_length)
    data_etos[:] = np.nan
else:
    pass
if input_etrs.size == 0:
    data_etrs = np.zeros(data_length)
    data_etrs[:] = np.nan
else:
    pass

# Create Datetime dataframe for reindexing
datetime_df = pd.DataFrame({'year': data_year, 'month': data_month, 'day': data_day})
datetime_df = pd.to_datetime(datetime_df[['month', 'day', 'year']])
# Create a series of all dates in time series
date_reindex = pd.date_range(datetime_df.iloc[0], datetime_df.iloc[-1])

# Create dataframe of data
data_df = pd.DataFrame({'date': datetime_df, 'year': data_year, 'month': data_month, 'day': data_day,
                        'tavg': data_tavg, 'tmax': data_tmax, 'tmin': data_tmin, 'tdew': data_tdew,
                        'vappres': data_vappres, 'rhavg': data_rhavg, 'rhmax': data_rhmax, 'rhmin': data_rhmin,
                        'rs': data_rs, 'ws': data_ws, 'precip': data_precip,
                        'data_eto': data_etos, 'data_etr': data_etrs}, index=datetime_df)

# Check for the existence of duplicate indexes
# if found, since it cannot be determined which value is true, we default to first instance and remove all following
data_df = data_df[~data_df.index.duplicated(keep='first')]

# Reindex data with filled date series
data_df = data_df.reindex(date_reindex, fill_value=np.nan)

# Now that data has been resampled to fill in missing time series,
# extract individual vars back to numpy arrays.
# Also fill in Y/M/D vars so they don't have nan values
data_tavg = np.array(data_df.tavg)
data_tmax = np.array(data_df.tmax)
data_tmin = np.array(data_df.tmin)
data_tdew = np.array(data_df.tdew)
data_vappres = np.array(data_df.vappres)
data_rhavg = np.array(data_df.rhavg)
data_rhmax = np.array(data_df.rhmax)
data_rhmin = np.array(data_df.rhmin)
data_rs = np.array(data_df.rs)
data_ws = np.array(data_df.ws)
data_precip = np.array(data_df.precip)
data_etos = np.array(data_df.data_eto)
data_etrs = np.array(data_df.data_etr)
# Fill in these with the pandas date_range calculation so they don't have NaNs
data_year = np.array(date_reindex.year)
data_month = np.array(date_reindex.month)
data_day = np.array(date_reindex.day)
# Recreate DOY now that we possibly have more dates
data_length = data_month.shape[0]
data_doy = []

for i in range(data_length):
    data_doy.append(dt.date(data_year[i], data_month[i], data_day[i]).strftime("%j"))

data_doy = list(map(int, data_doy))

# Convert to np arrays
data_doy = np.array(data_doy)
# End of Dataframe Resampling Section
########################################################################################################################

########################################################################################################################
# Secondary variable generation - @SVG
# This section calculates all of the secondary variables needed for ET calculation, and figures out how to calculate
# based on what variables are provided
print("\nSystem: Now calculating secondary variables based on data provided.")
print(dt.datetime.now())

station_pressure = 101.3 * (((293 - (0.0065 * station_elev)) / 293) ** 5.26)  # units kPa, EQ 3 in ASCE RefET manual

##########
# Humidity Section
# Figures out how to calculate both vapor pressure (ea) and dewpoint temperature (Tdew) if they are not provided.
calc_tdew = []  # dewpoint temperature
# Create tdew if we don't have it, using the best variables provided
if tdew_col == -1:  # We are not given TDew
    if vappres_col != -1:  # Vapor Pressure exists
        calc_ea = np.array(data_vappres)
        for i in range(data_length):
            # Calculate TDew using actual vapor pressure
            # Below equation was taken from the book "Evapotranspiration: Principles and Applications for Water
            # Management" by Goyal and Harmsen, and is equation 9 in chapter 13, page 320.
            calc_tdew.append((116.91 + (237.3 * np.log(calc_ea[i]))) / (16.78 - np.log(calc_ea[i])))

    elif vappres_col == -1 and rhmax_col != -1 and rhmin_col != -1:  # RHmax and RHmin exist so we use them for TDew
        eo_tmax = []  # saturation vapor pressure based on tmax, units kPa, EQ 7 in ASCE RefET manual
        eo_tmin = []  # saturation vapor pressure based on tmin, units kPa, EQ 7 in ASCE RefET manual
        calc_ea = []  # actual vapor pressure, units kPa, EQ 11 in ASCE RefET manual
        for i in range(data_length):
            # We first estimate Ea using RHMax and Min, and then use calculated EA to calculate TDew
            eo_tmax.append(0.6108 * np.exp((17.27 * data_tmax[i]) / (data_tmax[i] + 237.3)))  # EQ 7
            eo_tmin.append(0.6108 * np.exp((17.27 * data_tmin[i]) / (data_tmin[i] + 237.3)))  # EQ 7
            calc_ea.append((eo_tmin[i] * (data_rhmax[i] / 100)) + (eo_tmax[i] * (data_rhmin[i] / 100)) / 2)  # EQ 11
            calc_tdew.append((116.91 + (237.3 * np.log(calc_ea[i]))) / (16.78 - np.log(calc_ea[i])))  # Cited above
    else:
        # Because we are not given actual Vapor Pressure or RHMax/RHmin, we use RH Avg to calculate Ea and then TDew
        eo_tavg = []  # saturation vapor pressure based on tavg, units kPa, EQ 7 in ASCE RefET manual
        calc_ea = []  # actual vapor pressure, units kPa, EQ 14 in ASCE RefET manual
        calc_tdew = []
        for i in range(data_length):
            # Estimate Tdew using ea, actual vapor pressure
            eo_tavg.append(0.6108 * np.exp((17.27 * data_tavg[i]) / (data_tavg[i] + 237.3)))  # EQ 7
            calc_ea.append((data_rhavg[i] / 100) * eo_tavg[i])  # EQ 14
            calc_tdew.append((116.91 + (237.3 * np.log(calc_ea[i]))) / (16.78 - np.log(calc_ea[i])))  # Cited above

    data_tdew = np.array(calc_tdew)
    calc_ea = np.array(calc_ea)

else:
    # We are given tdew, so now we need to check for and calculate vapor pressure
    data_tdew = np.array(data_tdew)

    if vappres_col == -1:  # Vapor pressure not given, have to approximate from tdew
        calc_ea = np.array(0.6108 * np.exp((17.27 * data_tdew) / (data_tdew + 237.3)))  # EQ 8, units kPa
    else:
        # Vapor pressure and tdew were both provided so we don't need to calculate either.
        calc_ea = np.array(data_vappres)

##########
# Temperature Section
# Figures secondary temperature values and mean monthly counterparts for use downstream
# Generate tmax-tmin and tmin-tdew
tmax_tmin = []  # temperature difference between tmax and tmin
tmin_tdew = []  # temperature difference between tmin and tdew
monthly_deltat = []  # monthly averaged temperature difference, across all years, so 12 values
monthly_tmin_tdew = []  # monthly averaged tmin-tdew difference, across all years, so 12 values
for i in range(data_length):
    tmax_tmin.append(data_tmax[i] - data_tmin[i])
    tmin_tdew.append(data_tmin[i] - data_tdew[i])

tmax_tmin = np.array(tmax_tmin)
tmin_tdew = np.array(tmin_tdew)
# Create average monthly temperature and monthly tmin-tdew for downstream analysis
k = 1
while k <= 12:
    temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
    temp_indexes = np.array(temp_indexes)

    temp_value = np.nanmean(tmax_tmin[temp_indexes])
    monthly_deltat.append(temp_value)

    temp_value = np.nanmean(tmin_tdew[temp_indexes])
    monthly_tmin_tdew.append(temp_value)
    k += 1
# Convert into numpy arrays
monthly_deltat = np.array(monthly_deltat)
monthly_tmin_tdew = np.array(monthly_tmin_tdew)

##########
# Solar Radiation and Evapotranspiration Section
# Now that secondary temperature variables are taken care of, we will calculate Rs variables and ETrs/ETos
rso_d = np.empty(data_length)  # Clear sky solar radiation
rs_tr = np.empty(data_length)  # Thornton-Running solar radiation approximation.
calc_etos = np.empty(data_length)
calc_etrs = np.empty(data_length)

# Due to incorporating Open-ET/RefET package, I am copying some variables while changing their units to satisfy what
# the RefET package requires
# Rs EQ below from https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
refet_rs = np.array(data_rs * 0.0864)  # convert W/m2 to  MJ/m2,

print("\nSystem: Now calculating rs_tr, rso, ETos, and ETrs.")
print(dt.datetime.now())
for i in range(data_length):
    temp_month = data_month[i] - 1  # pulling the current month, shifted by 1 for index

    # Calculating Thornton-Running estimated solar radiation and Clear sky solar radiation
    (rso_d[i], rs_tr[i]) = emprso_w_tr(station_lat, station_pressure, calc_ea[i], data_doy[i],
                                       monthly_deltat[temp_month], tmax_tmin[i])

    # Calculating ETo in mm using refET package
    calc_etos[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i], uz=data_ws[i],
                               zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                               doy=data_doy[i], method='asce').eto()

    # Calculating ETr in mm using refET package
    calc_etrs[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i], uz=data_ws[i],
                               zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                               doy=data_doy[i], method='asce').etr()

# Convert rs_tr and rso to w/m2
rso_d *= 11.574
rs_tr *= 11.574

##########
# Mean Monthly Generation
# Create all other mean monthly values for downstream analysis
print("\nSystem: Now calculating mean monthly values for generated secondary variables.")
print(dt.datetime.now())

monthly_calc_etos = []
monthly_calc_etrs = []
monthly_data_etos = []
monthly_data_etrs = []
monthly_data_ws = []
monthly_data_tmin = []
monthly_data_tdew = []
monthly_data_rs = []
monthly_rs_tr = []
mm_dt_array = []

k = 1
while k <= 12:
    temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
    temp_indexes = np.array(temp_indexes)

    temp_value = np.nanmean(calc_etos[temp_indexes])
    monthly_calc_etos.append(temp_value)

    temp_value = np.nanmean(calc_etrs[temp_indexes])
    monthly_calc_etrs.append(temp_value)

    if etos_col != -1:
        temp_value = np.nanmean(data_etos[temp_indexes])
        monthly_data_etos.append(temp_value)
    else:
        pass

    if etrs_col != -1:
        temp_value = np.nanmean(data_etrs[temp_indexes])
        monthly_data_etrs.append(temp_value)
    else:
        pass

    temp_value = np.nanmean(data_ws[temp_indexes])
    monthly_data_ws.append(temp_value)

    temp_value = np.nanmean(data_tmin[temp_indexes])
    monthly_data_tmin.append(temp_value)

    temp_value = np.nanmean(data_tdew[temp_indexes])
    monthly_data_tdew.append(temp_value)

    temp_value = np.nanmean(data_rs[temp_indexes])
    monthly_data_rs.append(temp_value)

    temp_value = np.nanmean(rs_tr[temp_indexes])
    monthly_rs_tr.append(temp_value)

    mm_dt_array.append(k)

    k += 1

monthly_calc_etos = np.array(monthly_calc_etos)
monthly_calc_etrs = np.array(monthly_calc_etrs)
monthly_data_etos = np.array(monthly_data_etos)
monthly_data_etrs = np.array(monthly_data_etrs)
monthly_data_ws = np.array(monthly_data_ws)
monthly_data_tmin = np.array(monthly_data_tmin)
monthly_data_tdew = np.array(monthly_data_tdew)
monthly_data_rs = np.array(monthly_data_rs)
monthly_rs_tr = np.array(monthly_rs_tr)

print("\nSystem: Done calculating all secondary variables.")
print(dt.datetime.now())
# End of secondary data generation
########################################################################################################################

# ######################################################################################################################
# Original data backup - @ODB
# save backup file to the same directory as original file path
# Also create backups of original data before correction to show how much (%) the data was corrected in output file
backup_file = station_name + "_backup" + ".csv"

output_header = (
    "Year, Month, Day, TAvg (C), Tmax (C), Tmin (C), Tdew (C), Vapor Pressure (kPa), "
    "RH Avg (%), RH Max (%), RH Min (%), Rs (W/m2), Rs TR (W/m2), Rso (W/m2), "
    "Ws (m/s), Precip (mm), Data ETrs(mm), Data ETos(mm), Calc ETrs(mm), Calc ETos(mm)"
)

np.savetxt(
    backup_file, np.c_[
        data_year, data_month, data_day, data_tavg, data_tmax, data_tmin, data_tdew, data_vappres,
        data_rhavg, data_rhmax, data_rhmin, data_rs, rs_tr, rso_d, data_ws,
        data_precip, data_etrs, data_etos, calc_etrs, calc_etos
    ], fmt='%1.3f', delimiter=',', header=output_header
)

##########
# Create original data variables
# These variables exist to be compared with their after-correction data to see how far (what %) the data has changed
# These percentages will be written to an output file.
orig_tavg = data_tavg
orig_tmax = data_tmax
orig_tmin = data_tmin
orig_tdew = data_tdew
orig_vappres = data_vappres
orig_rhavg = data_rhavg
orig_rhmax = data_rhmax
orig_rhmin = data_rhmin
orig_rs = data_rs
orig_rs_tr = rs_tr
orig_rso_d = rso_d
orig_ws = data_ws
orig_precip = data_precip
orig_data_etrs = data_etrs
orig_data_etos = data_etos
orig_calc_etrs = calc_etrs
orig_calc_etos = calc_etos

# End of original data backup
########################################################################################################################

# ######################################################################################################################
# Script mode section - @SMS
# This section figures out which method of correction the user wants to apply and then does so.
# First check to see if correction flag has been checked, if not, just display the data in bokeh and close.
# If correction has been selected, set looping variable to true.
script_mode = data_config['MODES'].getboolean('script_mode')  # 0 for looking, 1 for correction
corr_mode = data_config['MODES'].getboolean('correction_mode')  # 0 for manual, 1 for .ini presets
disp_bokeh = data_config['MODES'].getboolean('bokeh_plots')  # 0 for not generating, 1 for showing
et_plot = data_config['MODES'].getboolean('et_comparison_plot')  # 0 for not generating, 1 for showing
rh_plot = data_config['DATA'].getboolean('vappress_rhplot_flag')  # 0 for not generating, 1 for showing
correction_bl = 0  # flag for correction later on that gets changed by ini file preference
ini_corr = 0  # flag for correction later on that gets changed by ini file preference

# Create datetime array for display with data
dt_array = []
for i in range(data_length):
    dt_array.append(dt.datetime(data_year[i], data_month[i], data_day[i]))
dt_array = np.array(dt_array, dtype=np.datetime64)
data_null = np.empty(data_length) * np.nan

##########
# Script mode selection
# If user chooses not to correct (script_mode == 0) then script will generate graphs of the data and then close
# Graph displays regardless of disp_bokeh setting in ini file, as otherwise the examine data mode wouldn't work
if not script_mode:

    ###########
    # BOKEH ET comparison graph
    if et_plot:  # This graph is only generated if user wants provided station ET compared to calculated ET

        x_size = 600
        y_size = 450
        output_file(station_name + "_ET_comparison_pre_correction.html")

        et1 = figure(
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='mm', title="Etos",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        et1.line(dt_array, data_etos, line_color="blue", legend="Data")
        et1.line(dt_array, calc_etos, line_color="black", legend="Calc")
        et1.legend.location = "bottom_left"

        et2 = figure(
            x_range=et1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='mm', title="Etrs",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        et2.line(dt_array, data_etrs, line_color="blue", legend="Data")
        et2.line(dt_array, calc_etrs, line_color="black", legend="Calc")
        et2.legend.location = "bottom_left"

        et3 = figure(
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='mm', title="MM Etos",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        et3.line(mm_dt_array, monthly_data_etos, line_color="blue", legend="MM data")
        et3.line(mm_dt_array, monthly_calc_etos, line_color="black", legend="MM calc")
        et3.legend.location = "bottom_left"

        et4 = figure(
            x_range=et3.x_range,
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='mm', title="MM Etrs",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        et4.line(mm_dt_array, monthly_data_etrs, line_color="blue", legend="MM data")
        et4.line(mm_dt_array, monthly_calc_etrs, line_color="black", legend="MM calc")
        et4.legend.location = "bottom_left"

        figET = gridplot([[et1, et2], [et3, et4]], toolbar_location="left")
        save(figET)

        print("\nSystem: Bokeh figure comparing station ET and calculated ET has been generated.")
        print(dt.datetime.now())
    else:
        pass

    ##########
    # BOKEH All data graph
    # Generates a bokeh display of all data, while determining which humidity variable (subplot 4) to plot

    x_size = 500
    y_size = 350
    output_file(station_name + "_pre_correction_output.html")

    s1 = figure(
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='Celsius', title="Tmax and Tmin",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s1.line(dt_array, data_tmax, line_color="red", legend="Data TMax")
    s1.line(dt_array, data_tmin, line_color="blue", legend="Data TMin")
    s1.legend.location = "bottom_left"

    s2 = figure(
        x_range=s1.x_range,
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='Celsius', title="Tmin and Tdew",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s2.line(dt_array, data_tmin, line_color="blue", legend="Data TMin")
    s2.line(dt_array, data_tdew, line_color="black", legend="Data TDew")
    s2.legend.location = "bottom_left"

    s3 = figure(
        x_range=s1.x_range,
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='m/s', title="Windspeed",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s3.line(dt_array, data_ws, line_color="black", legend="Windspeed")
    s3.legend.location = "bottom_left"

    # Subplot 4 changes based on what variables are provided
    if vappres_col != -1:  # Vapor pressure exist
        s4 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='kPa', title="Vapor Pressure",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s4.line(dt_array, calc_ea, line_color="black", legend="Vapor Pressure")
        s4.legend.location = "bottom_left"
    elif vappres_col == -1 and rhmax_col != -1 and rhmin_col != -1:  # RHmax and RHmin exist
        s4 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='%', title="RH Max and Min",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s4.line(dt_array, data_rhmax, line_color="black", legend="RH Max")
        s4.line(dt_array, data_rhmin, line_color="blue", legend="RH Min")
        s4.legend.location = "bottom_left"
    elif rhavg_col != -1:  # RHavg exists
        s4 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='%', title="RH Average",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s4.line(dt_array, data_rhavg, line_color="black", legend="RH Avg")
        s4.legend.location = "bottom_left"
    else:  # only TDew was provided
        # TODO allow for calc_ea plot when calc'd from tdew?
        # in mean time just display tdew
        s4 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Celsius', title="Dewpoint Temperature",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s4.line(dt_array, data_tdew, line_color="black", legend="Data TDew")
        s4.legend.location = "bottom_left"

    s5 = figure(
        x_range=s1.x_range,
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='mm', title="Precipitation",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s5.line(dt_array, data_precip, line_color="black", legend="Precipitation")
    s5.legend.location = "bottom_left"

    s6 = figure(
        x_range=s1.x_range,
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='W/m2', title="Rs and Rso",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s6.line(dt_array, data_rs, line_color="blue", legend="Rs")
    s6.line(dt_array, rso_d, line_color="black", legend="Rso")
    s6.legend.location = "bottom_left"

    s7 = figure(
        width=x_size, height=y_size,
        x_axis_label='Month', y_axis_label='W/m2', title="MM Rs and Rs TR",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s7.line(mm_dt_array, monthly_data_rs, line_color="blue", legend="MM Rs")
    s7.line(mm_dt_array, monthly_rs_tr, line_color="black", legend="MM Rs TR")
    s7.legend.location = "bottom_left"

    s8 = figure(
        x_range=s7.x_range,
        width=x_size, height=y_size,
        x_axis_label='Month', y_axis_label='Celsius', title="MM Tmin and Tdew",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s8.line(mm_dt_array, monthly_data_tmin, line_color="blue", legend="MM Tmin")
    s8.line(mm_dt_array, monthly_data_tdew, line_color="black", legend="MM Tdew")
    s8.legend.location = "bottom_left"

    s9 = figure(
        x_range=s7.x_range,
        width=x_size, height=y_size,
        x_axis_label='Month', y_axis_label='Celsius', title="MM Tmin - Tdew",
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    s9.line(mm_dt_array, monthly_tmin_tdew, line_color="black", legend="MM Tmin - Tdew")
    s9.legend.location = "bottom_left"

    if rh_plot:
        # user wants to see RH plot in addition to viewing vapor pressure
        s10 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='%', title="RHMax and Min",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s10.line(dt_array, data_rhmax, line_color="black", legend="RH Max")
        s10.line(dt_array, data_rhmin, line_color="blue", legend="RH Min")
        s10.legend.location = "bottom_left"

        fig = gridplot([[s1, s2, s3], [s4, s5, s6], [s7, s8, s9], [s10]], toolbar_location="left")
        save(fig)
    else:
        fig = gridplot([[s1, s2, s3], [s4, s5, s6], [s7, s8, s9]], toolbar_location="left")
        save(fig)

    print("\nSystem: Bokeh figure displaying data before correction has been generated and saved in directory.")
    print(dt.datetime.now())

# For these below options to trigger, script mode must be set to 1, indicating the user wishes to correct data
elif not corr_mode:  # manual correction using terminal window
    correction_bl = 1
    ini_corr = 0
else:  # corrections applied from .ini file presets
    ini_corr = 1
    correction_bl = 0

# ######################################################################################################################
# Manual Correction Section - @MCS
# Execute loop repeatedly until user is done correcting variables
while correction_bl == 1:
    reset_output()  # clears bokeh output, prevents ballooning file sizes
    print('\nPlease select which of the following variables you want to correct'
          '\n   Enter 1 for TMax and TMin.'
          '\n   Enter 2 for TMin and TDew.'
          '\n   Enter 3 for Windspeed.'
          '\n   Enter 4 for Rs.'
          '\n   Enter 5 for Humidity Measurements (Vapor Pressure, RHMax and RHmin, or RHAvg.)'
          '\n   Enter 6 for Precipitation.'
          '\n   Enter 7 to stop applying corrections.'
          )

    user = int(input("\nEnter your selection: "))
    loop = 1
    while loop:
        if 1 <= user <= 7:
            loop = 0
        else:
            print('Please enter a valid option.')
            user = int(input('Specify which variable you would like to correct: '))

    # Correcting Temperature data
    if user == 1 or user == 2:

        if user == 1:
            # Tmax and Tmin
            (data_tmax, data_tmin) = correction(station_name, log_file, data_tmax, 'TMax', data_tmin,
                                                'TMin', dt_array, data_month, data_year, 1)
        else:
            # Tmin and Tdew
            (data_tmin, data_tdew) = correction(station_name, log_file, data_tmin, 'TMin', data_tdew,
                                                'TDew', dt_array, data_month, data_year, 1)

        # Due to temperature being corrected, most secondary variables have to be corrected.
        # Code below is taken from the secondary variable generation section - @SVG
        print("\nSystem: Now recalculating secondary variables now that temperature has been corrected.")
        print(dt.datetime.now())

        # Check to see if we were given vapor pressure, if not, then recalculate it from corrected tdew
        if vappres_col == -1:  # Vapor pressure not given, have to approximate from tdew
            calc_ea = np.array(0.6108 * np.exp((17.27 * data_tdew) / (data_tdew + 237.3)))  # EQ 8, units kPa
        else:
            calc_ea = np.array(data_vappres)

        ##########
        # Temperature Section
        # Figures secondary temperature values and mean monthly counterparts for use downstream
        # Generate tmax-tmin and tmin-tdew
        tmax_tmin = []  # temperature difference between tmax and tmin
        tmin_tdew = []  # temperature difference between tmin and tdew
        monthly_deltat = []  # monthly averaged temperature difference, across all years, so 12 values
        monthly_tmin_tdew = []  # monthly averaged tmin-tdew difference, across all years, so 12 values
        for i in range(data_length):
            tmax_tmin.append(data_tmax[i] - data_tmin[i])
            tmin_tdew.append(data_tmin[i] - data_tdew[i])

        tmax_tmin = np.array(tmax_tmin)
        tmin_tdew = np.array(tmin_tdew)

        # Create average monthly temperature and monthly tmin-tdew for downstream analysis
        k = 1
        while k <= 12:
            temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
            temp_indexes = np.array(temp_indexes)

            temp_value = np.nanmean(tmax_tmin[temp_indexes])
            monthly_deltat.append(temp_value)

            temp_value = np.nanmean(tmin_tdew[temp_indexes])
            monthly_tmin_tdew.append(temp_value)
            k += 1
        monthly_deltat = np.array(monthly_deltat)
        monthly_tmin_tdew = np.array(monthly_tmin_tdew)

        ##########
        # Solar Radiation and Evapotranspiration Section
        # Now that secondary temperature variables are taken care of, we will calculate Rs variables and ETrs/ETos
        rso_d = np.empty(data_length)  # Clear sky solar radiation
        rs_tr = np.empty(data_length)  # Thornton-Running solar radiation approximation.
        calc_etos = np.empty(data_length)
        calc_etrs = np.empty(data_length)

        # Due to incorporating Open-ET/RefET package, I am copying some variables while changing their units
        # to satisfy what the RefET package requires
        # Rs EQ below from https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
        refet_rs = np.array(data_rs * 0.0864)  # convert W/m2 to  MJ/m2,

        print("\nSystem: Now recalculating rs_tr, rso, ETos, and ETrs.")
        print(dt.datetime.now())
        for i in range(data_length):
            temp_month = data_month[i] - 1  # pulling the current month, shifted by 1 for index

            # Calculating Thornton-Running estimated solar radiation and Clear sky solar radiation
            (rso_d[i], rs_tr[i]) = emprso_w_tr(station_lat, station_pressure, calc_ea[i], data_doy[i],
                                               monthly_deltat[temp_month], tmax_tmin[i])

            # Calculating ETo in mm using refET package
            calc_etos[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').eto()

            # Calculating ETr in mm using refET package
            calc_etrs[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').etr()

        # Convert rs_tr and rso to w/m2
        rso_d *= 11.574
        rs_tr *= 11.574

        ##########
        # Mean Monthly Generation
        # Create all other mean monthly values for downstream analysis
        monthly_calc_etos = []
        monthly_calc_etrs = []
        monthly_data_tmin = []
        monthly_data_tdew = []
        monthly_rs_tr = []

        k = 1
        while k <= 12:
            temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
            temp_indexes = np.array(temp_indexes)

            temp_value = np.nanmean(calc_etos[temp_indexes])
            monthly_calc_etos.append(temp_value)

            temp_value = np.nanmean(calc_etrs[temp_indexes])
            monthly_calc_etrs.append(temp_value)

            temp_value = np.nanmean(data_tmin[temp_indexes])
            monthly_data_tmin.append(temp_value)

            temp_value = np.nanmean(data_tdew[temp_indexes])
            monthly_data_tdew.append(temp_value)

            temp_value = np.nanmean(rs_tr[temp_indexes])
            monthly_rs_tr.append(temp_value)

            k += 1

        monthly_calc_etos = np.array(monthly_calc_etos)
        monthly_calc_etrs = np.array(monthly_calc_etrs)
        monthly_data_ws = np.array(monthly_data_ws)
        monthly_data_tmin = np.array(monthly_data_tmin)
        monthly_data_tdew = np.array(monthly_data_tdew)
        monthly_data_rs = np.array(monthly_data_rs)
        monthly_rs_tr = np.array(monthly_rs_tr)

        print("\nSystem: Done recalculating all secondary variables.")
        print(dt.datetime.now())

    # Correcting Windspeed
    elif user == 3:
        (data_ws, data_null) = correction(station_name, log_file, data_ws, 'Ws', data_null, 'NONE', dt_array, data_month,
                                          data_year, 4)

        # After correcting windspeed, we need to regenerate downstream variables.
        print("\nSystem: Now recalculating secondary variables now that wind speed has been corrected.")
        print(dt.datetime.now())

        # Code is again taken from @SVG section
        calc_etos = np.empty(data_length)
        calc_etrs = np.empty(data_length)

        # Due to incorporating Open-ET/RefET package, I am copying some variables while changing their units
        # to satisfy what the RefET package requires
        # Rs EQ below from https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
        refet_rs = np.array(data_rs * 0.0864)  # convert W/m2 to  MJ/m2,

        print("\nSystem: Now recalculating ETos and ETrs.")
        print(dt.datetime.now())
        for i in range(data_length):
            temp_month = data_month[i] - 1  # pulling the current month, shifted by 1 for index

            # Calculating ETo in mm using refET package
            calc_etos[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').eto()

            # Calculating ETr in mm using refET package
            calc_etrs[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').etr()

        monthly_calc_etrs = []
        monthly_calc_etos = []
        monthly_data_ws = []

        k = 1
        while k <= 12:
            temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
            temp_indexes = np.array(temp_indexes)

            temp_value = np.nanmean(calc_etrs[temp_indexes])
            monthly_calc_etrs.append(temp_value)

            temp_value = np.nanmean(calc_etos[temp_indexes])
            monthly_calc_etos.append(temp_value)

            temp_value = np.nanmean(data_ws[temp_indexes])
            monthly_data_ws.append(temp_value)

            k += 1

        monthly_calc_etos = np.array(monthly_calc_etos)
        monthly_calc_etrs = np.array(monthly_calc_etrs)
        monthly_data_ws = np.array(monthly_data_ws)
        print("\nSystem: Done recalculating all secondary variables.")
        print(dt.datetime.now())

    # Solar radiation
    elif user == 4:
        (data_rs, data_null) = correction(station_name, log_file, data_rs, 'Rs', rso_d, 'Rso', dt_array, data_month, data_year, 3)

        print("\nSystem: Now recalculating secondary variables now that solar radiation has been corrected.")
        print(dt.datetime.now())

        # Code is again taken from @SVG section
        calc_etos = np.empty(data_length)
        calc_etrs = np.empty(data_length)

        # Due to incorporating Open-ET/RefET package, I am copying some variables while changing their units
        # to satisfy what the RefET package requires
        # Rs EQ below from https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
        refet_rs = np.array(data_rs * 0.0864)  # convert W/m2 to  MJ/m2,

        print("\nSystem: Now recalculating ETos and ETrs.")
        print(dt.datetime.now())
        for i in range(data_length):
            temp_month = data_month[i] - 1  # pulling the current month, shifted by 1 for index

            # Calculating ETo in mm using refET package
            calc_etos[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').eto()

            # Calculating ETr in mm using refET package
            calc_etrs[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').etr()

        monthly_calc_etrs = []
        monthly_calc_etos = []
        monthly_data_rs = []

        k = 1
        while k <= 12:
            temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
            temp_indexes = np.array(temp_indexes)

            temp_value = np.nanmean(calc_etrs[temp_indexes])
            monthly_calc_etrs.append(temp_value)

            temp_value = np.nanmean(calc_etos[temp_indexes])
            monthly_calc_etos.append(temp_value)

            temp_value = np.nanmean(data_rs[temp_indexes])
            monthly_data_rs.append(temp_value)

            k += 1

        monthly_calc_etos = np.array(monthly_calc_etos)
        monthly_calc_etrs = np.array(monthly_calc_etrs)
        monthly_data_rs = np.array(monthly_data_rs)
        print("\nSystem: Done recalculating all secondary variables.")
        print(dt.datetime.now())

    # Humidity
    elif user == 5:

        if vappres_col != -1:  # Vapor Pressure exists
            (data_vappres, data_null) = correction(station_name, log_file, data_vappres, 'Vapor Pressure', data_null, 'NONE',
                                                   dt_array, data_month, data_year, 4)
        elif vappres_col == -1 and rhmax_col != -1 and rhmin_col != -1:
            (data_rhmax, data_rhmin) = correction(station_name, log_file, data_rhmax, 'RHMax', data_rhmin,
                                                  'RHMin', dt_array, data_month, data_year, 2)
        else:  # Have to use RH Avg to calculate Ea
            (data_rhavg, data_null) = correction(station_name, log_file, data_rhavg, 'RHAvg', data_null, 'NONE',
                                                 dt_array, data_month, data_year, 4)

        # Due to humidity being corrected, most secondary variables have to be corrected.
        # Code below is taken from the secondary variable generation section - @SVG
        print("\nSystem: Now recalculating secondary variables now that humidity has been corrected.")
        print(dt.datetime.now())

        ##########
        # Humidity Section
        # Figures out how to calculate both vapor pressure (ea) and dewpoint temperature (Tdew) if they are not provided
        calc_tdew = []  # dewpoint temperature
        # Create tdew if we don't have it, using the best variables provided
        if tdew_col == -1:  # We are not given TDew
            if vappres_col != -1:  # Vapor Pressure exists
                calc_ea = np.array(data_vappres)
                for i in range(data_length):
                    # Calculate TDew using actual vapor pressure
                    # Below equation was taken from the book "Evapotranspiration: Principles and Applications for Water
                    # Management" by Goyal and Harmsen, and is equation 9 in chapter 13, page 320.
                    calc_tdew.append((116.91 + (237.3 * np.log(calc_ea[i]))) / (16.78 - np.log(calc_ea[i])))

            elif vappres_col == -1 and rhmax_col != -1 and rhmin_col != -1:  # RHmax and RHmin exist
                eo_tmax = []  # saturation vapor pressure based on tmax, units kPa, EQ 7 in ASCE RefET manual
                eo_tmin = []  # saturation vapor pressure based on tmin, units kPa, EQ 7 in ASCE RefET manual
                calc_ea = []  # actual vapor pressure, units kPa, EQ 11 in ASCE RefET manual
                for i in range(data_length):
                    # We first estimate Ea using RHMax and Min, and then use calculated EA to calculate TDew
                    eo_tmax.append(0.6108 * np.exp((17.27 * data_tmax[i]) / (data_tmax[i] + 237.3)))  # EQ 7
                    eo_tmin.append(0.6108 * np.exp((17.27 * data_tmin[i]) / (data_tmin[i] + 237.3)))  # EQ 7
                    calc_ea.append((eo_tmin[i] * (data_rhmax[i] / 100)) + (eo_tmax[i] * (data_rhmin[i] / 100)) / 2)
                    calc_tdew.append((116.91 + (237.3 * np.log(calc_ea[i]))) / (16.78 - np.log(calc_ea[i])))
            else:
                # Because we are not given actual Vapor Pressure or RHMax/RHmin, we use RH Avg to calculate Ea/Tdew
                eo_tavg = []  # saturation vapor pressure based on tavg, units kPa, EQ 7 in ASCE RefET manual
                calc_ea = []  # actual vapor pressure, units kPa, EQ 14 in ASCE RefET manual
                calc_tdew = []
                for i in range(data_length):
                    # Estimate Tdew using ea, actual vapor pressure
                    eo_tavg.append(0.6108 * np.exp((17.27 * data_tavg[i]) / (data_tavg[i] + 237.3)))  # EQ 7
                    calc_ea.append((data_rhavg[i] / 100) * eo_tavg[i])  # EQ 14
                    calc_tdew.append(
                        (116.91 + (237.3 * np.log(calc_ea[i]))) / (16.78 - np.log(calc_ea[i])))  # Cited above

            data_tdew = np.array(calc_tdew)
            calc_ea = np.array(calc_ea)

        else:
            # We are given tdew, so now we need to check for and calculate vapor pressure
            data_tdew = np.array(data_tdew)

            if vappres_col == -1:  # Vapor pressure not given, have to approximate from tdew
                calc_ea = np.array(0.6108 * np.exp((17.27 * data_tdew) / (data_tdew + 237.3)))  # EQ 8, units kPa
            else:
                # Vapor pressure and tdew were both provided so we don't need to calculate either.
                calc_ea = np.array(data_vappres)

        ##########
        # Temperature Section
        # Figures secondary temperature values and mean monthly counterparts for use downstream
        # Generate tmax-tmin and tmin-tdew
        tmax_tmin = []  # temperature difference between tmax and tmin
        tmin_tdew = []  # temperature difference between tmin and tdew
        monthly_deltat = []  # monthly averaged temperature difference, across all years, so 12 values
        monthly_tmin_tdew = []  # monthly averaged tmin-tdew difference, across all years, so 12 values
        for i in range(data_length):
            tmax_tmin.append(data_tmax[i] - data_tmin[i])
            tmin_tdew.append(data_tmin[i] - data_tdew[i])

        tmax_tmin = np.array(tmax_tmin)
        tmin_tdew = np.array(tmin_tdew)
        # Create average monthly temperature and monthly tmin-tdew for downstream analysis
        k = 1
        while k <= 12:
            temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
            temp_indexes = np.array(temp_indexes)

            temp_value = np.nanmean(tmax_tmin[temp_indexes])
            monthly_deltat.append(temp_value)

            temp_value = np.nanmean(tmin_tdew[temp_indexes])
            monthly_tmin_tdew.append(temp_value)
            k += 1
        # Convert into numpy arrays
        monthly_deltat = np.array(monthly_deltat)
        monthly_tmin_tdew = np.array(monthly_tmin_tdew)

        ##########
        # Solar Radiation and Evapotranspiration Section
        # Now that secondary temperature variables are taken care of, we will calculate Rs variables and ETrs/ETos
        rso_d = np.empty(data_length)  # Clear sky solar radiation
        rs_tr = np.empty(data_length)  # Thornton-Running solar radiation approximation.
        calc_etos = np.empty(data_length)
        calc_etrs = np.empty(data_length)

        # Due to incorporating Open-ET/RefET package, I am copying some variables while changing their units to satisfy
        # what the RefET package requires
        # Rs EQ below from https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
        refet_rs = np.array(data_rs * 0.0864)  # convert W/m2 to  MJ/m2,

        print("\nSystem: Now recalculating rs_tr, rso, ETos, and ETrs.")
        print(dt.datetime.now())
        for i in range(data_length):
            temp_month = data_month[i] - 1  # pulling the current month, shifted by 1 for index

            # Calculating Thornton-Running estimated solar radiation and Clear sky solar radiation
            (rso_d[i], rs_tr[i]) = emprso_w_tr(station_lat, station_pressure, calc_ea[i], data_doy[i],
                                               monthly_deltat[temp_month], tmax_tmin[i])

            # Calculating ETo in mm using refET package
            calc_etos[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').eto()

            # Calculating ETr in mm using refET package
            calc_etrs[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                       uz=data_ws[i],
                                       zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                       doy=data_doy[i], method='asce').etr()

        # Convert rs_tr and rso to w/m2
        rso_d *= 11.574
        rs_tr *= 11.574

        ##########
        # Mean Monthly Generation
        # Create all other mean monthly values for downstream analysis
        print("\nSystem: Now recalculating mean monthly values for generated secondary variables.")
        print(dt.datetime.now())

        monthly_calc_etos = []
        monthly_calc_etrs = []
        monthly_data_ws = []
        monthly_data_tmin = []
        monthly_data_tdew = []
        monthly_data_rs = []
        monthly_rs_tr = []
        mm_dt_array = []

        k = 1
        while k <= 12:
            temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
            temp_indexes = np.array(temp_indexes)

            temp_value = np.nanmean(calc_etos[temp_indexes])
            monthly_calc_etos.append(temp_value)

            temp_value = np.nanmean(calc_etrs[temp_indexes])
            monthly_calc_etrs.append(temp_value)

            temp_value = np.nanmean(data_ws[temp_indexes])
            monthly_data_ws.append(temp_value)

            temp_value = np.nanmean(data_tmin[temp_indexes])
            monthly_data_tmin.append(temp_value)

            temp_value = np.nanmean(data_tdew[temp_indexes])
            monthly_data_tdew.append(temp_value)

            temp_value = np.nanmean(data_rs[temp_indexes])
            monthly_data_rs.append(temp_value)

            temp_value = np.nanmean(rs_tr[temp_indexes])
            monthly_rs_tr.append(temp_value)

            mm_dt_array.append(k)

            k += 1

        monthly_calc_etos = np.array(monthly_calc_etos)
        monthly_calc_etrs = np.array(monthly_calc_etrs)
        monthly_data_ws = np.array(monthly_data_ws)
        monthly_data_tmin = np.array(monthly_data_tmin)
        monthly_data_tdew = np.array(monthly_data_tdew)
        monthly_data_rs = np.array(monthly_data_rs)
        monthly_rs_tr = np.array(monthly_rs_tr)

        print("\nSystem: Done recalculating all secondary variables.")
        print(dt.datetime.now())

    # Precipitation
    elif user == 6:
        (data_precip, data_null) = correction(station_name, log_file, data_precip, 'Precip', data_null, 'NONE',
                                              dt_array, data_month, data_year, 4)

        monthly_data_precip = []

        k = 1
        while k <= 12:
            temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
            temp_indexes = np.array(temp_indexes)

            temp_value = np.nanmean(data_precip[temp_indexes])
            monthly_data_precip.append(temp_value)

            k += 1

    else:
        # user quits, set looping boolean to false
        print('\n System: Exiting corrections.')
        correction_bl = 0

    # ##################################################################################################################
    # BOKEH all data correction graph
    if disp_bokeh:
        x_size = 500
        y_size = 350
        output_file(station_name + "_complete_corrections_graph.html")

        s1 = figure(
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Celsius', title="Tmax and Tmin",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s1.line(dt_array, data_tmax, line_color="red", legend="Data TMax")
        s1.line(dt_array, data_tmin, line_color="blue", legend="Data TMin")
        s1.legend.location = "bottom_left"

        s2 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Celsius', title="Tmin and Tdew",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s2.line(dt_array, data_tmin, line_color="blue", legend="Data TMin")
        s2.line(dt_array, data_tdew, line_color="black", legend="Data TDew")
        s2.legend.location = "bottom_left"

        s3 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='m/s', title="Windspeed",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s3.line(dt_array, data_ws, line_color="black", legend="Windspeed")
        s3.legend.location = "bottom_left"

        # Subplot 4 changes based on what variables are provided
        if vappres_col != -1:  # Vapor pressure exist
            s4 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='kPa', title="Vapor Pressure",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s4.line(dt_array, calc_ea, line_color="black", legend="Vapor Pressure")
            s4.legend.location = "bottom_left"
        elif vappres_col == -1 and rhmax_col != -1 and rhmin_col != -1:  # RHmax and RHmin exist
            s4 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='%', title="RH Max and Min",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s4.line(dt_array, data_rhmax, line_color="black", legend="RH Max")
            s4.line(dt_array, data_rhmin, line_color="blue", legend="RH Min")
            s4.legend.location = "bottom_left"
        elif vappres_col == -1 and rhavg_col != -1:  # RHavg exists
            s4 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='%', title="RH Average",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s4.line(dt_array, data_rhavg, line_color="black", legend="RH Avg")
            s4.legend.location = "bottom_left"
        else:  # only TDew of Vapor Pressure was provided
            # TODO allow for calc_ea plot when calc'd from tdew?
            # in mean time just display tdew
            s4 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='Celsius', title="Dewpoint Temperature",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s4.line(dt_array, data_tdew, line_color="black", legend="Data TDew")
            s4.legend.location = "bottom_left"

        s5 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='mm', title="Precipitation",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s5.line(dt_array, data_precip, line_color="black", legend="Precipitation")
        s5.legend.location = "bottom_left"

        s6 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='W/m2', title="Rs and Rso",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s6.line(dt_array, data_rs, line_color="blue", legend="Rs")
        s6.line(dt_array, rso_d, line_color="black", legend="Rso")
        s6.legend.location = "bottom_left"

        s7 = figure(
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='W/m2', title="MM Rs and Rs TR",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s7.line(mm_dt_array, monthly_data_rs, line_color="blue", legend="MM Rs")
        s7.line(mm_dt_array, monthly_rs_tr, line_color="black", legend="MM Rs TR")
        s7.legend.location = "bottom_left"

        s8 = figure(
            x_range=s7.x_range,
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='Celsius', title="MM Tmin and Tdew",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s8.line(mm_dt_array, monthly_data_tmin, line_color="blue", legend="MM Tmin")
        s8.line(mm_dt_array, monthly_data_tdew, line_color="black", legend="MM Tdew")
        s8.legend.location = "bottom_left"

        s9 = figure(
            x_range=s7.x_range,
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='Celsius', title="MM Tmin - Tdew",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s9.line(mm_dt_array, monthly_tmin_tdew, line_color="black", legend="MM Tmin - Tdew")
        s9.legend.location = "bottom_left"

        if rh_plot:
            # user wants to see RH plot in addition to viewing vapor pressure
            s10 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='%', title="RHMax and Min",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s10.line(dt_array, data_rhmax, line_color="black", legend="RH Max")
            s10.line(dt_array, data_rhmin, line_color="blue", legend="RH Min")
            s10.legend.location = "bottom_left"

            fig = gridplot([[s1, s2, s3], [s4, s5, s6], [s7, s8, s9], [s10]], toolbar_location="left")
            save(fig)
        else:
            fig = gridplot([[s1, s2, s3], [s4, s5, s6], [s7, s8, s9]], toolbar_location="left")
            save(fig)

        print("\nSystem: Bokeh figure displaying corrected data has been generated and saved in directory.")
        print(dt.datetime.now())

        # ##############################################################################################################
        # BOKEH ET comparison graph
        if et_plot:
            x_size = 600
            y_size = 450
            output_file(station_name + "_ET_comparison_post_correction.html")

            et1 = figure(
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='mm', title="Etos",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et1.line(dt_array, data_etos, line_color="blue", legend="Data")
            et1.line(dt_array, calc_etos, line_color="black", legend="Calc")
            et1.legend.location = "bottom_left"

            et2 = figure(
                x_range=et1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='mm', title="Etrs",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et2.line(dt_array, data_etrs, line_color="blue", legend="Data")
            et2.line(dt_array, calc_etrs, line_color="black", legend="Calc")
            et2.legend.location = "bottom_left"

            et3 = figure(
                width=x_size, height=y_size,
                x_axis_label='Month', y_axis_label='mm', title="MM Etos",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et3.line(mm_dt_array, monthly_data_etos, line_color="blue", legend="MM data")
            et3.line(mm_dt_array, monthly_calc_etos, line_color="black", legend="MM calc")
            et3.legend.location = "bottom_left"

            et4 = figure(
                x_range=et3.x_range,
                width=x_size, height=y_size,
                x_axis_label='Month', y_axis_label='mm', title="MM Etrs",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et4.line(mm_dt_array, monthly_data_etrs, line_color="blue", legend="MM data")
            et4.line(mm_dt_array, monthly_calc_etrs, line_color="black", legend="MM calc")
            et4.legend.location = "bottom_left"

            figET = gridplot([[et1, et2], [et3, et4]], toolbar_location="left")
            save(figET)

            print("\nSystem: Bokeh figure comparing station ET and calculated ET has been generated.")
            print(dt.datetime.now())
        else:
            pass
    else:
        pass

# ######################################################################################################################
# INI Correction Section - @ACS
# Step through all variables and correct them using .ini file presets
# Order is as follows:
# Correct TMax and TMin using dual pass MM brackets for outliers
# Correct RH using year-based percentile corrections
# Correct TMin and TDew using dual pass MM brackets for outliers
# Recalculate Rso for Rs correction
# Correct Rs based on periodic percentiles
# Recalculate RefET values and close

# TODO add methods of correction for RHAvg, Ws, VapPress, Precip
# TODO find a way to auto-adjust VapPress based on year-based RHmax/min corrections?

if ini_corr == 1:
    tmax_tmin_corr_flag = data_config['CORRECTIONS'].getboolean('tmax_tmin_corr_flag')
    tmin_tdew_corr_flag = data_config['CORRECTIONS'].getboolean('tmin_tdew_corr_flag')
    rhmax_min_corr_flag = data_config['CORRECTIONS'].getboolean('rhmax_min_corr_flag')
    rs_corr_flag = data_config['CORRECTIONS'].getboolean('rs_corr_flag')

    ####################################################################################################################
    # Correct Tmax and Tmin, then recalculate downstream variables
    if tmax_tmin_corr_flag == 1:  # Tmax and Tmin
        (data_tmax, data_tmin) = ini_correction(station_name, log_file, data_tmax, 'TMax', data_tmin,
                                                'TMin', dt_array, data_month, data_year, 1)
    else:
        pass

    # Recalculate all downstream variables now that temperature has been corrected
    tmax_tmin = data_tmax - data_tmin
    tmin_tdew = data_tmin - data_tdew

    ####################################################################################################################
    # Correct RHmax and RHmin
    if rhmax_min_corr_flag == 1:  # RHmax and RHmin
        (data_rhmax, data_rhmin) = ini_correction(station_name, log_file, data_rhmax, 'RHMax', data_rhmin,
                                                  'RHMin', dt_array, data_month, data_year, 2)
    else:
        pass

    # Recalculate TDew if it was not provided in input file
    if tdew_col == -1:  # No TDew
        eo_tmax = []  # vapor pressure based on tmax, units kpa
        eo_tmin = []  # vapor pressure based on tmin, units kpa
        calc_ea = []  # actual vapor pressure, based off eo values and RHmax and RHmin
        calc_tdew = []  # dewpoint temperature

        if rhmax_col != -1 and rhmin_col != -1:  # RHmax and RHmin exist so we can calculate TDew
            for i in range(data_length):
                # Estimate Tdew using ea, actual vapor pressure
                eo_tmax.append(0.6108 * np.exp((17.27 * data_tmax[i]) / (data_tmax[i] + 237.3)))
                eo_tmin.append(0.6108 * np.exp((17.27 * data_tmin[i]) / (data_tmin[i] + 237.3)))
                calc_ea.append((eo_tmin[i] * (data_rhmax[i] / 100)) + (eo_tmax[i] * (data_rhmin[i] / 100)) / 2)
                calc_tdew.append((116.91 + 237.3 * np.log(calc_ea[i])) / (16.78 - np.log(calc_ea[i])))
        else:
            pass  # TODO include TDEW from RHAVG calculation

        data_tdew = np.array(calc_tdew)
        calc_ea = np.array(calc_ea)
    else:
        # If TDew is provided, then calculating it with RH data would be inferior
        pass

    ####################################################################################################################
    # Correct Tmin, and Tdew, then recalculate downstream variables
    if tmin_tdew_corr_flag == 1:  # Tmin and Tdew
        (data_tmin, data_tdew) = ini_correction(station_name, log_file, data_tmin, 'TMin', data_tdew,
                                                'TDew', dt_array, data_month, data_year, 1)
    else:
        pass

    # Recalculate all downstream variables now that temperature has been corrected
    tmax_tmin = data_tmax - data_tmin
    tmin_tdew = data_tmin - data_tdew
    monthly_deltat = []
    monthly_tmin_tdew = []
    monthly_data_tmin = []
    monthly_data_tdew = []

    if tdew_col != -1:
        # calc_ea is calculated here based off of tdew, whereas above it is calculated based on RHmax/min
        calc_ea = np.array(0.6108 * np.exp((17.27 * data_tdew) / (data_tdew + 237.3)))
    else:
        pass

    k = 1
    while k <= 12:
        temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
        temp_indexes = np.array(temp_indexes)

        temp_value = np.nanmean(tmax_tmin[temp_indexes])
        monthly_deltat.append(temp_value)

        temp_value = np.nanmean(tmin_tdew[temp_indexes])
        monthly_tmin_tdew.append(temp_value)

        temp_value = np.nanmean(data_tmin[temp_indexes])
        monthly_data_tmin.append(temp_value)

        temp_value = np.nanmean(data_tdew[temp_indexes])
        monthly_data_tdew.append(temp_value)

        k += 1

    monthly_deltat = np.array(monthly_deltat)

    ####################################################################################################################
    # Recalculating rso for rs correction now that upstream vars have been corrected
    rso_d = np.empty(data_length)  # Clear sky solar radiation
    rs_tr = np.empty(data_length)  # Thornton-Running solar radiation approximation.
    for i in range(data_length):
        temp_month = data_month[i] - 1  # pulling the current month, shifted by 1 for index

        # Calculating Thornton-Running estimated solar radiation and Clear sky solar radiation
        (rso_d[i], rs_tr[i]) = emprso_w_tr(station_lat, station_pressure, calc_ea[i], data_doy[i],
                                           monthly_deltat[temp_month], tmax_tmin[i])

    # convert rs_tr and rso to w/m2
    rso_d *= 11.574
    rs_tr *= 11.574

    rso_d = np.array(rso_d)
    rs_tr = np.array(rs_tr)

    ####################################################################################################################
    # Correcting Solar Radiation
    if rs_corr_flag == 1:  # Rs
        (data_rs, data_null) = ini_correction(station_name, log_file, data_rs, 'Rs', rso_d, 'Rso', dt_array, data_month,
                                              data_year, 3)
    else:
        pass

    monthly_data_rs = []
    monthly_rs_tr = []

    k = 1
    while k <= 12:
        temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
        temp_indexes = np.array(temp_indexes)

        temp_value = np.nanmean(data_rs[temp_indexes])
        monthly_data_rs.append(temp_value)

        temp_value = np.nanmean(rs_tr[temp_indexes])
        monthly_rs_tr.append(temp_value)

        k += 1

    ####################################################################################################################
    # Recalculating ET now that upstream vars have been corrected
    calc_etos = np.empty(data_length)
    calc_etrs = np.empty(data_length)

    # Due to incorporating Open-ET/RefET package, I am copying some variables while changing their units to satisfy
    # what the RefET package requires
    # Rs EQ below from https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
    refet_rs = np.array(data_rs * 0.0864)  # convert W/m2 to  MJ/m2,

    for i in range(data_length):
        temp_month = data_month[i] - 1  # pulling the current month, shifted by 1 for index

        # Calculating ETo in mm using refET package
        calc_etos[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                   uz=data_ws[i],
                                   zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                   doy=data_doy[i], method='asce').eto()

        # Calculating ETr in mm using refET package
        calc_etrs[i] = refet.Daily(tmin=data_tmin[i], tmax=data_tmax[i], ea=calc_ea[i], rs=refet_rs[i],
                                   uz=data_ws[i],
                                   zw=ws_anemometer_height, elev=station_elev, lat=station_lat,
                                   doy=data_doy[i], method='asce').etr()

    monthly_calc_etos = []
    monthly_calc_etrs = []

    k = 1
    while k <= 12:
        temp_indexes = [ex for ex, ind in enumerate(data_month) if ind == k]
        temp_indexes = np.array(temp_indexes)

        temp_value = np.nanmean(calc_etos[temp_indexes])
        monthly_calc_etos.append(temp_value)

        temp_value = np.nanmean(calc_etrs[temp_indexes])
        monthly_calc_etrs.append(temp_value)

        k += 1

    ####################################################################################################################
    # Retype everything as a numpy array to prevent bokeh crashes, JSON will crash if a list is all nans
    monthly_deltat = np.array(monthly_deltat)
    monthly_tmin_tdew = np.array(monthly_tmin_tdew)
    monthly_data_tmin = np.array(monthly_data_tmin)
    monthly_data_tdew = np.array(monthly_data_tdew)
    monthly_data_rs = np.array(monthly_data_rs)
    monthly_rs_tr = np.array(monthly_rs_tr)
    monthly_calc_etos = np.array(monthly_calc_etos)
    monthly_calc_etrs = np.array(monthly_calc_etrs)

    # ##################################################################################################################
    # BOKEH all data correction graph
    if disp_bokeh:
        x_size = 500
        y_size = 350
        output_file(station_name + "_complete_corrections_graph.html")

        s1 = figure(
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Celsius', title="Tmax and Tmin",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s1.line(dt_array, data_tmax, line_color="red", legend="Data TMax")
        s1.line(dt_array, data_tmin, line_color="blue", legend="Data TMin")
        s1.legend.location = "bottom_left"

        s2 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Celsius', title="Tmin and Tdew",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s2.line(dt_array, data_tmin, line_color="blue", legend="Data TMin")
        s2.line(dt_array, data_tdew, line_color="black", legend="Data TDew")
        s2.legend.location = "bottom_left"

        s3 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='m/s', title="Windspeed",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s3.line(dt_array, data_ws, line_color="black", legend="Windspeed")
        s3.legend.location = "bottom_left"
        # TODO no vapor pressure, fix the language on the first onces first then copy down here
        # Subplot 4 changes based on what variables are provided
        if rhmax_col != -1 and rhmin_col != -1:  # RHmax and RHmin exist
            s4 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='%', title="RH Max and Min",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s4.line(dt_array, data_rhmax, line_color="black", legend="RH Max")
            s4.line(dt_array, data_rhmin, line_color="blue", legend="RH Min")
            s4.legend.location = "bottom_left"
        elif rhavg_col != -1:  # RHavg exists
            s4 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='%', title="RH Average",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s4.line(dt_array, data_rhavg, line_color="black", legend="RH Avg")
            s4.legend.location = "bottom_left"
        else:  # only TDew of Vapor Pressure was provided
            # TODO allow for calc_ea plot when calc'd from tdew?
            # in mean time just display tdew
            s4 = figure(
                x_range=s1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='Celsius', title="Dewpoint Temperature",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            s4.line(dt_array, data_tdew, line_color="black", legend="Data TDew")
            s4.legend.location = "bottom_left"

        s5 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='mm', title="Precipitation",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s5.line(dt_array, data_precip, line_color="black", legend="Precipitation")
        s5.legend.location = "bottom_left"

        s6 = figure(
            x_range=s1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='W/m2', title="Rs and Rso",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s6.line(dt_array, data_rs, line_color="blue", legend="Rs")
        s6.line(dt_array, rso_d, line_color="black", legend="Rso")
        s6.legend.location = "bottom_left"

        s7 = figure(
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='W/m2', title="MM Rs and Rs TR",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s7.line(mm_dt_array, monthly_data_rs, line_color="blue", legend="MM Rs")
        s7.line(mm_dt_array, monthly_rs_tr, line_color="black", legend="MM Rs TR")
        s7.legend.location = "bottom_left"

        s8 = figure(
            x_range=s7.x_range,
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='Celsius', title="MM Tmin and Tdew",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s8.line(mm_dt_array, monthly_data_tmin, line_color="blue", legend="MM Tmin")
        s8.line(mm_dt_array, monthly_data_tdew, line_color="black", legend="MM Tdew")
        s8.legend.location = "bottom_left"

        s9 = figure(
            x_range=s7.x_range,
            width=x_size, height=y_size,
            x_axis_label='Month', y_axis_label='Celsius', title="MM Tmin - Tdew",
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        s9.line(mm_dt_array, monthly_tmin_tdew, line_color="black", legend="MM Tmin - Tdew")
        s9.legend.location = "bottom_left"

        fig = gridplot([[s1, s2, s3], [s4, s5, s6], [s7, s8, s9]], toolbar_location="left")
        save(fig)

        print("\nSystem: Bokeh figure displaying corrected data has been generated and saved in directory.")
        print(dt.datetime.now())

        # ######################################################################################################################
        # BOKEH ET comparison graph
        if et_plot:
            x_size = 600
            y_size = 450
            output_file("correction_et_comp.html")

            et1 = figure(
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='mm', title="Etos",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et1.line(dt_array, data_etos, line_color="blue", legend="Data")
            et1.line(dt_array, calc_etos, line_color="black", legend="Calc")
            et1.legend.location = "bottom_left"

            et2 = figure(
                x_range=et1.x_range,
                width=x_size, height=y_size, x_axis_type="datetime",
                x_axis_label='Timestep', y_axis_label='mm', title="Etrs",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et2.line(dt_array, data_etrs, line_color="blue", legend="Data")
            et2.line(dt_array, calc_etrs, line_color="black", legend="Calc")
            et2.legend.location = "bottom_left"

            et3 = figure(
                width=x_size, height=y_size,
                x_axis_label='Month', y_axis_label='mm', title="MM Etos",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et3.line(mm_dt_array, monthly_data_etos, line_color="blue", legend="MM data")
            et3.line(mm_dt_array, monthly_calc_etos, line_color="black", legend="MM calc")
            et3.legend.location = "bottom_left"

            et4 = figure(
                x_range=et3.x_range,
                width=x_size, height=y_size,
                x_axis_label='Month', y_axis_label='mm', title="MM Etrs",
                tools='pan, box_zoom, undo, reset, hover, save'
            )
            et4.line(mm_dt_array, monthly_data_etrs, line_color="blue", legend="MM data")
            et4.line(mm_dt_array, monthly_calc_etrs, line_color="black", legend="MM calc")
            et4.legend.location = "bottom_left"

            figET = gridplot([[et1, et2], [et3, et4]], toolbar_location="left")
            save(figET)

            print("\nSystem: Bokeh figure comparing station ET and calculated ET has been generated.")
            print(dt.datetime.now())
        else:
            pass
    else:
        pass
# ######################################################################################################################
# Save data to an output file, xls in this case so we can have a second sheet with differences
# Data is saved regardless of script mode given above.

# First create corrected-original delta numpy arrays
diff_tavg = np.array(data_tavg - orig_tavg)
diff_tmax = np.array(data_tmax - orig_tmax)
diff_tmin = np.array(data_tmin - orig_tmin)
diff_tdew = np.array(data_tdew - orig_tdew)
diff_vappres = np.array(data_vappres - orig_vappres)
diff_rhavg = np.array(data_rhavg - orig_rhavg)
diff_rhmax = np.array(data_rhmax - orig_rhmax)
diff_rhmin = np.array(data_rhmin - orig_rhmin)
diff_rs = np.array(data_rs - orig_rs)
diff_rs_tr = np.array(rs_tr - orig_rs_tr)
diff_rso = np.array(rso_d - orig_rso_d)
diff_ws = np.array(data_ws - orig_ws)
diff_precip = np.array(data_precip - orig_precip)
diff_data_etrs = np.array(data_etrs - orig_data_etrs)
diff_data_etos = np.array(data_etos - orig_data_etos)
diff_calc_etrs = np.array(calc_etrs - orig_calc_etrs)
diff_calc_etos = np.array(calc_etos - orig_calc_etos)

# Create datetime for output dataframe
datetime_df = pd.DataFrame({'year': data_year, 'month': data_month, 'day': data_day})
datetime_df = pd.to_datetime(datetime_df[['month', 'day', 'year']])
# Create column sequence so pandas prints file in correct order
colseq = ['year', 'month', 'day', 'TAvg (C)', 'TMax (C)', 'TMin (C)', 'TDew (C)', 'Vapor Pres (kPa)',
          'RHAvg (%)', 'RHMax (%)', 'RHMin (%)', 'Rs (w/m2)', 'Rs_TR (w/m2)', 'Rso (w/m2)',
          'Windspeed (m/s)', 'Precip (mm)', 'Data_ETr (mm)', 'Data_ETo (mm)', 'Calc_ETr (mm)', 'Calc_ETo (mm)']

# Create output dataframe
outdata_df = pd.DataFrame({'date': datetime_df, 'year': data_year, 'month': data_month, 'day': data_day,
                           'TAvg (C)': data_tavg, 'TMax (C)': data_tmax, 'TMin (C)': data_tmin, 'TDew (C)': data_tdew,
                           'Vapor Pres (kPa)': data_vappres, 'RHAvg (%)': data_rhavg, 'RHMax (%)': data_rhmax,
                           'RHMin (%)': data_rhmin, 'Rs (w/m2)': data_rs, 'Rs_TR (w/m2)': rs_tr, 'Rso (w/m2)': rso_d,
                           'Windspeed (m/s)': data_ws, 'Precip (mm)': data_precip, 'Data_ETr (mm)': data_etrs,
                           'Data_ETo (mm)': data_etos, 'Calc_ETr (mm)': calc_etrs, 'Calc_ETo (mm)': calc_etos},
                          index=datetime_df)
# Creating difference dataframe
diffdata_df = pd.DataFrame({'date': datetime_df, 'year': data_year, 'month': data_month, 'day': data_day,
                            'TAvg (C)': diff_tavg, 'TMax (C)': diff_tmax, 'TMin (C)': diff_tmin, 'TDew (C)': diff_tdew,
                            'Vapor Pres (kPa)': diff_vappres, 'RHAvg (%)': diff_rhavg, 'RHMax (%)': diff_rhmax,
                            'RHMin (%)': diff_rhmin, 'Rs (w/m2)': diff_rs, 'Rs_TR (w/m2)': diff_rs_tr,
                            'Rso (w/m2)': diff_rso, 'Windspeed (m/s)': diff_ws, 'Precip (mm)': diff_precip,
                            'Data_ETr (mm)': diff_data_etrs, 'Data_ETo (mm)': diff_data_etos,
                            'Calc_ETr (mm)': diff_calc_etrs, 'Calc_ETo (mm)': diff_calc_etos},
                           index=datetime_df)

outdata_df = outdata_df.reindex(columns=colseq)
diffdata_df = diffdata_df.reindex(columns=colseq)

# Open up pandas excel writer
outwriter = pd.ExcelWriter(station_name + "_output" + ".xlsx", engine='xlsxwriter')
# Convert data frames to xlsxwriter excel objects
outdata_df.to_excel(outwriter, sheet_name='Corrected Data', na_rep=missing_fill_value)
diffdata_df.to_excel(outwriter, sheet_name='Delta (Corr - Orig)', na_rep=missing_fill_value)
# Save output file
outwriter.save()

print("\nSystem: Ending script and closing log file.")
print(dt.datetime.now())

logger = open(log_file, 'a')
logger.write('The file has been successfully processed and output files saved at %s. \n' % dt.datetime.now().strftime(
                                                                                           "%Y-%m-%d %H:%M:%S"))
logger.close()
if log_bool:
    log_file.close()
else:
    pass
