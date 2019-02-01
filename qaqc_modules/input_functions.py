import configparser as cp
import datetime as dt
import logging as log
import numpy as np
import pandas as pd


def extract_variable(raw_data, col):
    """
        Pulls individual variable from raw data array and returns it as a numpy array.

        Parameters:
            raw_data : 2D matrix of raw data pulled from input .csv file
            col : integer specifying column to pull out

        Returns:
            var : 1D numpy array of the individual variable
    """
    data_size = raw_data.shape[0]  # size of data set
    
    if col != -1:  # Column of -1 indicates variable isn't included in data
        var = np.array(raw_data[:, col].astype('float'))  # Needs to be typed as float for numpy nans in dataset
    else:
        var = np.zeros(data_size)
        var[:] = np.nan

    return var


def convert_units(config_file_path, data, var_type):
    """
        Converts passed variable to the correct units for the rest of the script.
        Actions taken are dependant on variable flags set in config file

        Parameters:
            config_file_path : path to configuration file
            data : 1D numpy array of variable to be converted
            var_type : string identifier of variable, used to pull the right unit flags

        Returns:
            converted_data : 1D numpy array of the data in the right units
    """

    converted_data = np.array(data)  # If we don't have to convert units then just return original data

    unit_config = cp.ConfigParser()
    unit_config.read(config_file_path)

    var_type = var_type.lower()

    if var_type == 'maximum temperature':
        tmax_f_flag = unit_config['DATA'].getboolean('tmax_f_flag')
        tmax_k_flag = unit_config['DATA'].getboolean('tmax_k_flag')

        if tmax_f_flag == 1 and tmax_k_flag == 0:  # Units Fahrenheit
            converted_data = np.array(((data - 32.0) * (5.0 / 9.0)))
        elif tmax_f_flag == 0 and tmax_k_flag == 1:  # Units Kelvin
            converted_data = np.array(data - 273.15)
        elif tmax_f_flag == 0 and tmax_k_flag == 0:  # Units Celsius
            pass
        else:
            # Incorrect setup of temperature flags, raise an error
            raise ValueError('Incorrect parameters: maximum temperature unit flags in config file are not correct.')
    elif var_type == 'minimum temperature':
        tmin_f_flag = unit_config['DATA'].getboolean('tmin_f_flag')
        tmin_k_flag = unit_config['DATA'].getboolean('tmin_k_flag')

        if tmin_f_flag == 1 and tmin_k_flag == 0:  # Units Fahrenheit
            converted_data = np.array(((data - 32.0) * (5.0 / 9.0)))
        elif tmin_f_flag == 0 and tmin_k_flag == 1:  # Units Kelvin
            converted_data = np.array(data - 273.15)
        elif tmin_f_flag == 0 and tmin_k_flag == 0:  # Units Celsius
            pass
        else:
            # Incorrect setup of temperature flags, raise an error
            raise ValueError('Incorrect parameters: minimum temperature unit flags in config file are not correct.')
    elif var_type == 'average temperature':
        tavg_f_flag = unit_config['DATA'].getboolean('tavg_f_flag')
        tavg_k_flag = unit_config['DATA'].getboolean('tavg_k_flag')

        if tavg_f_flag == 1 and tavg_k_flag == 0:  # Units Fahrenheit
            converted_data = np.array(((data - 32.0) * (5.0 / 9.0)))
        elif tavg_f_flag == 0 and tavg_k_flag == 1:  # Units Kelvin
            converted_data = np.array(data - 273.15)
        elif tavg_f_flag == 0 and tavg_k_flag == 0:  # Units Celsius
            pass
        else:
            # Incorrect setup of temperature flags, raise an error
            raise ValueError('Incorrect parameters: average temperature unit flags in config file are not correct.')
    elif var_type == 'dewpoint temperature':
        tdew_f_flag = unit_config['DATA'].getboolean('tdew_f_flag')
        tdew_k_flag = unit_config['DATA'].getboolean('tdew_k_flag')

        if tdew_f_flag == 1 and tdew_k_flag == 0:  # Units Fahrenheit
            converted_data = np.array(((data - 32.0) * (5.0 / 9.0)))
        elif tdew_f_flag == 0 and tdew_k_flag == 1:  # Units Kelvin
            converted_data = np.array(data - 273.15)
        elif tdew_f_flag == 0 and tdew_k_flag == 0:  # Units Celsius
            pass
        else:
            # Incorrect setup of temperature flags, raise an error
            raise ValueError('Incorrect parameters: dewpoint temperature unit flags in config file are not correct.')
    elif var_type == 'vapor pressure':
        ea_torr_flag = unit_config['DATA'].getboolean('ea_torr_flag')

        if ea_torr_flag == 1:  # Units torr or millimeters hydrogen
            converted_data = np.array(data * 0.133322)  # Converts to kPa
        else:
            pass
    elif var_type == 'wind speed':
        ws_mph_flag = unit_config['DATA'].getboolean('ws_mph_flag')

        if ws_mph_flag == 1:  # Miles per hour
            converted_data = np.array(data * 0.44704)  # Convert mph to m/s
        else:
            pass
    elif var_type == 'precipitation':
        precip_inch_flag = unit_config['DATA'].getboolean('precip_inch_flag')

        if precip_inch_flag == 1:  # Units inches
            converted_data = np.array(data * 25.4)  # Converts inches to mm
        else:
            pass
    elif var_type == 'maximum relative humidity':
        rhmax_fract_flag = unit_config['DATA'].getboolean('rhmax_fraction_flag')

        if rhmax_fract_flag == 1:  # Fraction (0.00-1.00) needs to be converted to a percentage
            converted_data = np.array(data * 100.0)
        else:
            pass
    elif var_type == 'minimum relative humidity':
        rhmin_fract_flag = unit_config['DATA'].getboolean('rhmin_fraction_flag')

        if rhmin_fract_flag == 1:  # Fraction (0.00-1.00) needs to be converted to a percentage
            converted_data = np.array(data * 100.0)
        else:
            pass
    elif var_type == 'average relative humidity':
        rhavg_fract_flag = unit_config['DATA'].getboolean('rhavg_fraction_flag')

        if rhavg_fract_flag == 1:  # Fraction (0.00-1.00) needs to be converted to a percentage
            converted_data = np.array(data * 100.0)
        else:
            pass
    elif var_type == 'solar radiation':
        rs_lang_flag = unit_config['DATA'].getboolean('rs_lang_flag')
        rs_mj_flag = unit_config['DATA'].getboolean('rs_mj_flag')
        rs_kw_hr_flag = unit_config['DATA'].getboolean('rs_kw_hr_flag')

        if rs_lang_flag == 1 and rs_mj_flag == 0 and rs_kw_hr_flag == 0:  # Units langleys
            converted_data = np.array(data * 0.48458)
        elif rs_lang_flag == 0 and rs_mj_flag == 1 and rs_kw_hr_flag == 0:  # Units MJ/m2
            converted_data = np.array(data * 11.574)
        elif rs_lang_flag == 0 and rs_mj_flag == 0 and rs_kw_hr_flag == 1:  # Units kw-hr
            converted_data = np.array((data * 1000) / 24)  # TODO: Find a better source for this equation
        elif rs_lang_flag == 0 and rs_mj_flag == 0 and rs_kw_hr_flag == 0:  # Units w/m2
            pass
        else:
            # Incorrect setup of temperature flags, raise an error
            raise ValueError('Incorrect parameters: solar radiation unit flags in config file are not correct.')
    else:
        # If an unsupported variable type is passed, raise a value error to point it out.
        raise ValueError('Unsupported variable type {} passed to convert_units function.'.format(var_type))

    return converted_data


def daily_realistic_limits(original_data, log_path, var_type):
    """
        Applies a realistic limit to data to automatically catch and remove bad values that may have resulted
        from sensor malfunctions, sensor degradation, etc. Caught values are replaced by a numpy nan. This function
        assumes all variables are already in metric units

        Parameters:
            original_data : 1D numpy array of original data from input file.
            log_path : path of the log file that is used to track how the data is modified
            var_type : string of text used to signify what type of data has been passed.

        Returns:
            limited_data : 1D numpy array of data after it has been checked for bad values.
    """
    clip_value = np.nan
    var_type = var_type.lower()

    limited_data = np.array(original_data)
    limited_data = limited_data.astype('float')  # np.nan is treated as a float so it needs to go into a float array

    np.warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning for nans in data

    if var_type in ['maximum temperature', 'minimum temperature', 'average temperature', 'dewpoint temperature']:
        limited_data[original_data <= -50] = clip_value  # -50 C is -58 F
        limited_data[original_data >= 60] = clip_value  # 60 C is 140 F
    elif var_type == 'wind speed':
        limited_data[original_data < 0] = clip_value  # Negative wind speed is impossible
        limited_data[original_data >= 70] = clip_value  # 70 m/s is a cat 5 hurricane
    elif var_type == 'precipitation':
        limited_data[original_data < 0] = clip_value  # Negative precipitation is impossible
        limited_data[original_data >= 610] = clip_value  # 610 mm is 2 ft of rain a day
    elif var_type == 'solar radiation':
        limited_data[original_data <= 5] = clip_value  # TODO: see if these Rs limits are acceptable
        limited_data[original_data >= 700] = clip_value
    elif var_type == 'vapor pressure':
        limited_data[original_data <= 0] = clip_value  # Negative vapor pressure is impossible
        limited_data[original_data >= 8] = clip_value  # TODO: see if this Ea limit is acceptable
    elif var_type in ['maximum relative humidity', 'minimum relative humidity', 'average relative humidity']:
        limited_data[original_data <= 2] = clip_value  # TODO: see if this RH limit is acceptable
        limited_data[original_data >= 100] = clip_value  # Relative humidity above 100% is impossible
    else:
        # If an unsupported variable type is passed, raise a value error to point it out.
        raise ValueError('Unsupported variable type {} passed to daily_realistic_limits function.'.format(var_type))

    # Count how many values were changed by this procedure and then write that to the log file
    mask = ~(np.isnan(original_data))  # create an inverse mask for when the original data has so they don't get counted
    num_clipped_values = np.sum(limited_data[mask] != original_data[mask])  # Count the values that were clipped out

    log.basicConfig()
    # Reopen log file to append corrections, then close it.
    corr_log = open(log_path, 'a')
    corr_log.write('%s %s values were removed for exceeding realistic limits. \n' % (num_clipped_values, var_type))
    corr_log.close()

    np.warnings.resetwarnings()  # reset warning filter to default
    return limited_data  # Return the limited data
    

def process_variable(config_file_path, raw_data, log_path, var_type):
    """
        Combines the functions extract_var, convert_units, and daily_realistic_limits to increase readability. First,
        the function extracts individual variables from the raw data, then converts them into the expected metric units,
        and finally sends them through a pass through filter to make sure there are no unrealistic values.
        Parameters:
            config_file_path : string of path to config file, should work with absolute or relative path
            raw_data : 2D matrix of raw data pulled from .csv specified in config file
            log_path : path of the log file that is used to track how the data is modified
            var_type : string of text used to signify what variable has been requested.

        Returns:
            filtered_var : 1D numpy array of variable that has been extracted, converted, and filtered
            var_col : column of pulled variable, used to track what is provided and what is calculated
    """
    var_config = cp.ConfigParser()
    var_config.read(config_file_path)

    var_type = var_type.lower()

    if var_type == 'maximum temperature':
        var_col = var_config['DATA'].getint('tmax_col')
    elif var_type == 'minimum temperature':
        var_col = var_config['DATA'].getint('tmin_col')
    elif var_type == 'average temperature':
        var_col = var_config['DATA'].getint('tavg_col')
    elif var_type == 'dewpoint temperature':
        var_col = var_config['DATA'].getint('tdew_col')
    elif var_type == 'maximum relative humidity':
        var_col = var_config['DATA'].getint('rhmax_col')
    elif var_type == 'minimum relative humidity':
        var_col = var_config['DATA'].getint('rhmin_col')
    elif var_type == 'average relative humidity':
        var_col = var_config['DATA'].getint('rhavg_col')
    elif var_type == 'vapor pressure':
        var_col = var_config['DATA'].getint('ea_col')
    elif var_type == 'wind speed':
        var_col = var_config['DATA'].getint('ws_col')
    elif var_type == 'precipitation':
        var_col = var_config['DATA'].getint('precip_col')
    elif var_type == 'solar radiation':
        var_col = var_config['DATA'].getint('rs_col')
    else:
        # If an unsupported variable type is passed, raise a value error to point it out.
        raise ValueError('Unsupported variable type {} passed to process_variable function.'.format(var_type))

    original_var = extract_variable(raw_data, var_col)  # Will either return data or an array of nans of expected size
    converted_var = convert_units(config_file_path, original_var, var_type)  # converts data to appropriate units
    filtered_var = daily_realistic_limits(converted_var, log_path, var_type)  # returns data filtered of bad values

    return filtered_var, var_col


def obtain_data(config_file_path):
    """
        Opens the config.ini file passed to this function, and from that reads the parameters for importing
        the dataset, including converting them to the correct units.

        Parameters:
            config_file_path : string of path to config file, should work with absolute or relative path

        Returns:
            extracted_data : pandas dataframe of entire dataset, with the variables being organized into columns
            station_parameters : 1D numpy array containing station metadata values
    """
    # Open config file
    config_file = cp.ConfigParser()
    config_file.read(config_file_path)
    print('\nSystem: Opening config file: %s' % config_file_path)

    #########################
    # METADATA and MODE parameters
    # Reads in metadata and opens data file to extract raw data

    file_path = config_file['METADATA']['data_file_path']
    station_lat = config_file['METADATA'].getfloat('station_latitude')  # Expected in decimal degrees
    station_elev = config_file['METADATA'].getfloat('station_elevation')  # Expected in meters
    anemom_height = config_file['METADATA'].getfloat('anemometer_height')  # Expected in meters
    fill_value = config_file['METADATA']['output_fill_value']  # Value for missing data in output file
    missing_data_value = config_file['METADATA']['missing_data_value']  # Value used to signify missing data in file
    lines_of_header = config_file['METADATA'].getint('lines_of_file_header')  # Lines of header in file to skip
    lines_of_footer = config_file['METADATA'].getint('lines_of_file_footer')  # Lines of footer in file to skip

    script_mode = config_file['MODES'].getboolean('script_mode')  # Option to either correct or view uncorrected data
    gen_bokeh = config_file['MODES'].getboolean('generate_plots')  # Option to generate bokeh plots or not

    station_text = file_path.split('.csv')  # Splitting file extension off of file name
    station_name = station_text[0]  # Name of file that will be attached to all of the outputs

    # read in data and trim it of header and footer
    raw_data = np.genfromtxt(file_path, dtype='U', delimiter=',', skip_header=lines_of_header,
                             skip_footer=lines_of_footer, autostrip=True)

    raw_rows = raw_data.shape[0]  # number of rows in data
    raw_cols = raw_data.shape[1]  # number of columns in data

    print("\nSystem: Raw data successfully read in.")
    # Create log file for this new data file
    log.basicConfig()
    log_file = station_name + "_changes_log" + ".txt"
    logger = open(log_file, 'w')
    logger.write('The raw data for %s has been successfully read in at %s. \n \n' %
                 (station_name, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    logger.close()

    # go through raw data and replace missing data values with nans
    # note that values will not be nan until list is typecast as a float
    for i in range(raw_rows):
        for j in range(raw_cols):
            if missing_data_value in raw_data[i, j]:
                raw_data[i, j] = np.nan
            else:
                pass

    #########################
    # Date handling
    # Figures out the date format and extracts from string if needed
    date_format = config_file['DATA'].getint('date_format')

    if date_format == 1:  # Date is provided as a string, expected format is MM/DD/YYYY, time can be included as well.
        date_col = config_file['DATA'].getint('date_col')
        date_time_included = config_file['DATA'].getboolean('date_time_included')  # see if HOURS:MINUTES was attached

        if date_col != -1:
            data_date = np.array(raw_data[:, date_col])
        else:
            # Script cannot function without a time variable
            raise ValueError('Missing parameter: pyWeatherQAQC requires date values in order to process data.')

        # Extract date information to produce DOY and serial date
        if date_time_included:
            date_format = "%m/%d/%Y %H:%M"
        else:
            date_format = "%m/%d/%Y"

        # TODO: test code below with stringdate dataset, probably won't work
        date_info = np.array(dt.datetime.strptime(data_date, date_format))
        data_day = np.array(date_info.day)
        data_month = np.array(date_info.month)
        data_year = np.array(date_info.year)

    elif date_format == 2:
        # Date is pre-split into several columns
        month_col = config_file['DATA'].getint('month_col')
        day_col = config_file['DATA'].getint('day_col')
        year_col = config_file['DATA'].getint('year_col')

        if month_col != -1 and day_col != -1 and year_col != -1:
            data_month = np.array(raw_data[:, month_col].astype('int'))
            data_day = np.array(raw_data[:, day_col].astype('int'))
            data_year = np.array(raw_data[:, year_col].astype('int'))
        else:
            # Script cannot function without a time variable
            raise ValueError('Parameter error: pyWeatherQAQC requires date values in order to process data.')
    else:
        # Script cannot function without a time variable
        raise ValueError('Parameter error: date_format is set to an unexpected value.')

    #########################
    # Variable processing
    # Imports all weather variables, converts them into the correct units, and filters them to remove impossible values

    (data_tmax, tmax_col) = process_variable(config_file_path, raw_data, log_file, 'maximum temperature')
    (data_tmin, tmin_col) = process_variable(config_file_path, raw_data, log_file, 'minimum temperature')
    (data_tavg, tavg_col) = process_variable(config_file_path, raw_data, log_file, 'average temperature')
    (data_tdew, tdew_col) = process_variable(config_file_path, raw_data, log_file, 'dewpoint temperature')
    (data_ea, ea_col) = process_variable(config_file_path, raw_data, log_file, 'vapor pressure')
    (data_rhmax, rhmax_col) = process_variable(config_file_path, raw_data, log_file, 'maximum relative humidity')
    (data_rhmin, rhmin_col) = process_variable(config_file_path, raw_data, log_file, 'minimum relative humidity')
    (data_rhavg, rhavg_col) = process_variable(config_file_path, raw_data, log_file, 'average relative humidity')
    (data_rs, rs_col) = process_variable(config_file_path, raw_data, log_file, 'solar radiation')
    (data_ws, ws_col) = process_variable(config_file_path, raw_data, log_file, 'wind speed')
    (data_precip, precip_col) = process_variable(config_file_path, raw_data, log_file, 'precipitation')

    # TODO: Track down this warning: C:\Anaconda3\lib\site-packages\numpy\core\_methods.py:32: RuntimeWarning:
    #  invalid value encountered in reduce return umr_minimum(a, axis, None, out, keepdims, initial)

    #########################
    # Dataframe Construction
    # In this section we convert the individual numpy arrays into a pandas dataframe to accomplish several goals:
    # 1. Make use of the pandas reindexing function to cover literal gaps in the dataset (not just missing values)
    # 2. Resample data to remove any duplicate records (same day appears twice in dataset, first instance is kept)
    # 3. Cleanly pass extracted data to the main script function

    # Create Datetime dataframe for reindexing
    datetime_df = pd.DataFrame({'year': data_year, 'month': data_month, 'day': data_day})
    datetime_df = pd.to_datetime(datetime_df[['month', 'day', 'year']])
    # Create a series of all dates in time series
    date_reindex = pd.date_range(datetime_df.iloc[0], datetime_df.iloc[-1])

    # Create dataframe of data
    data_df = pd.DataFrame({'date': datetime_df, 'year': data_year, 'month': data_month,
                            'day': data_day, 'tavg': data_tavg, 'tmax': data_tmax, 'tmin': data_tmin,
                            'tdew': data_tdew, 'ea': data_ea, 'rhavg': data_rhavg, 'rhmax': data_rhmax,
                            'rhmin': data_rhmin, 'rs': data_rs, 'ws': data_ws, 'precip': data_precip},
                           index=datetime_df)

    # Create dataframe of column indices for weather variable, to track which ones were provided vs calculated
    col_df = pd.Series({'tmax': tmax_col, 'tmin': tmin_col, 'tavg': tavg_col, 'tdew': tdew_col, 'ea': ea_col,
                        'rhmax': rhmax_col, 'rhmin': rhmin_col, 'rhavg': rhavg_col, 'rs': rs_col, 'ws': ws_col,
                        'precip': precip_col})

    # Check for the existence of duplicate indexes
    # if found, since it cannot be determined which value is true, we default to first instance and remove all following
    data_df = data_df[~data_df.index.duplicated(keep='first')]

    # Reindex data with filled date series in case there are gaps in the data
    data_df = data_df.reindex(date_reindex, fill_value=np.nan)

    # Now replace M/D/Y columns with reindexed dates so there are no missing days
    data_df.year = date_reindex.year
    data_df.month = date_reindex.month
    data_df.day = date_reindex.day

    return data_df, col_df, station_name, log_file, station_lat, station_elev, anemom_height, fill_value, \
           script_mode, gen_bokeh
