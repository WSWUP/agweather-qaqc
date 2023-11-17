import configparser as cp
import logging as log
import numpy as np
import os
import pandas as pd
import warnings

from agweatherqaqc.utils import validate_file


def read_config(config_file_path):
    """
    Opens config file at provided path and stores all required values in a python dictionary. This dictionary will be
    used both to import data and elsewhere in the code to refer to what type of data was passed in

    Args:
        config_file_path: string of path to config file

    Returns:
        config_dict: a dictionary of all required config file parameters

    """

    # Check to see if provided file exists and also that it is the correct type
    validate_file(config_file_path, 'ini')

    # Open ConfigParser and point it to file.
    config_reader = cp.ConfigParser()
    config_reader.read(config_file_path)

    # Create config file dictionary and start adding entries to it
    # METADATA Section
    config_dict = dict()
    config_dict['data_file_path'] = config_reader['METADATA']['DATA_FILE_PATH']
    config_dict['station_latitude'] = config_reader['METADATA'].getfloat('LATITUDE')  # Expected in DD not DMS
    config_dict['station_longitude'] = config_reader['METADATA'].getfloat('LONGITUDE')  # Expected in DD not DMS
    config_dict['station_elevation'] = config_reader['METADATA'].getfloat('ELEVATION')  # Expected in meters
    config_dict['anemometer_height'] = config_reader['METADATA'].getfloat('ANEMOMETER_HEIGHT')  # Expected in meters
    config_dict['missing_input_value'] = config_reader['METADATA']['MISSING_INPUT_VALUE']  # Input missing data
    config_dict['missing_output_value'] = config_reader['METADATA']['MISSING_OUTPUT_VALUE']  # Output missing data
    config_dict['lines_of_header'] = config_reader['METADATA'].getint('LINES_OF_HEADER')  # Lines of header to skip
    config_dict['lines_of_footer'] = config_reader['METADATA'].getint('LINES_OF_FOOTER')  # Lines of header to skip

    # OPTIONS Section
    config_dict['auto_flag'] = config_reader['OPTIONS'].getboolean('AUTOMATIC_OPTION')  # auto first iteration of QAQC
    config_dict['fill_flag'] = config_reader['OPTIONS'].getboolean('FILL_OPTION')  # Option to fill in missing data

    # DATA Section - Data Columns
    config_dict['date_format'] = config_reader['DATA'].getint('DATE_FORMAT')
    config_dict['string_date_col'] = config_reader['DATA'].getint('STRING_DATE_COL')
    config_dict['year_col'] = config_reader['DATA'].getint('YEAR_COL')
    config_dict['month_col'] = config_reader['DATA'].getint('MONTH_COL')
    config_dict['day_col'] = config_reader['DATA'].getint('DAY_COL')
    config_dict['day_of_year_col'] = config_reader['DATA'].getint('DAY_OF_YEAR_COL')
    config_dict['tmax_col'] = config_reader['DATA'].getint('TEMPERATURE_MAX_COL')
    config_dict['tavg_col'] = config_reader['DATA'].getint('TEMPERATURE_AVG_COL')
    config_dict['tmin_col'] = config_reader['DATA'].getint('TEMPERATURE_MIN_COL')
    config_dict['tdew_col'] = config_reader['DATA'].getint('DEWPOINT_TEMPERATURE_COL')
    config_dict['uz_col'] = config_reader['DATA'].getint('WIND_DATA_COL')
    config_dict['pp_col'] = config_reader['DATA'].getint('PRECIPITATION_COL')
    config_dict['rs_col'] = config_reader['DATA'].getint('SOLAR_RADIATION_COL')
    config_dict['ea_col'] = config_reader['DATA'].getint('VAPOR_PRESSURE_COL')
    config_dict['rhmax_col'] = config_reader['DATA'].getint('RELATIVE_HUMIDITY_MAX_COL')
    config_dict['rhavg_col'] = config_reader['DATA'].getint('RELATIVE_HUMIDITY_AVG_COL')
    config_dict['rhmin_col'] = config_reader['DATA'].getint('RELATIVE_HUMIDITY_MIN_COL')

    # DATA Section - Unit Flags
    config_dict['temperature_units'] = config_reader['DATA'].getint('TEMPERATURE_UNITS')
    config_dict['wind_units'] = config_reader['DATA'].getint('WIND_UNITS')
    config_dict['precipitation_units'] = config_reader['DATA'].getint('PRECIPITATION_UNITS')
    config_dict['solar_radiation_units'] = config_reader['DATA'].getint('SOLAR_RADIATION_UNITS')
    config_dict['vapor_pressure_units'] = config_reader['DATA'].getint('VAPOR_PRESSURE_UNITS')
    config_dict['relative_humidity_units'] = config_reader['DATA'].getint('RELATIVE_HUMIDITY_UNITS')

    # Check to see that all expected variables are provided, ConfigParser defaults to None if it can't find something.
    if None in config_dict.values():
        # Find all keys where value is None
        missing_keys = [key for (key, value) in config_dict.items() if value is None]
        raise ValueError('\n\nThe following required variables were missing values in the config file: {}.'
                         .format(missing_keys))
    else:
        return config_dict


def extract_variable(raw_data, col):
    """
        Pulls individual variable from raw data array and returns it as a numpy array.

        Args:
            raw_data : 2D matrix of raw data pulled from input .csv file
            col : integer specifying column to pull out

        Returns:
            var : 1D numpy array of the individual variable
    """
    data_size = raw_data.shape[0]  # size of data set
    if col != -1:  # Column of -1 indicates variable isn't included in data
        var = np.array(pd.to_numeric(raw_data.iloc[:, col], errors='coerce'))  # force all misc strings into NaN
    else:
        var = np.zeros(data_size)
        var[:] = np.nan

    return var


def convert_units(config_dict, original_data, var_type):
    """
    Takes in 1d numpy array of original data, and then converts it to the appropriate units.
    What actions are taken are dependant on what parameters were read in/stored into config_dict.

    Sources:
        https://www.wcc.nrcs.usda.gov/ftpref/wntsc/H&H/GEM/SolarRadConversion.pdf
        https://cliflo-niwa.niwa.co.nz/pls/niwp/wh.do_help?id=ls_rad
        FAO 56

    Args:
        config_dict: dictionary of all config file values
        original_data: 1d numpy array of original values
        var_type: string indicating what data type has been passed, ex. 'temperature', 'precipitation'

    Returns:
        converted_data: 1D numpy array of the converted values
    """

    converted_data = np.array(original_data)  # If we don't have to convert units then just return original data

    var_type = var_type.lower()

    if var_type == 'temperature':
        if config_dict['temperature_units'] == 0:  # Celsius
            pass
        elif config_dict['temperature_units'] == 1:  # Fahrenheit
            converted_data = np.array(((original_data - 32.0) * (5.0 / 9.0)))
        elif config_dict['temperature_units'] == 2:  # kelvin
            converted_data = np.array(original_data - 273.15)
        else:
            raise ValueError('Incorrect parameters: TEMPERATURE_UNITS in config is not set up correctly.')

    elif var_type == 'wind_speed':
        if config_dict['wind_units'] == 0:  # m/s
            pass
        elif config_dict['wind_units'] == 1:  # mph
            converted_data = np.array(original_data * 0.44704)
        elif config_dict['wind_units'] == 2:  # kmh
            converted_data = np.array(original_data * 0.27778)
        elif config_dict['wind_units'] == 3:  # wind run, miles per day
            converted_data = np.array((original_data * 1609.34) / 86400)  # miles to meters, day to seconds
        elif config_dict['wind_units'] == 4:  # wind run, kilometers per day
            converted_data = np.array((original_data * 1000) / 86400)  # kilometers to meters, day to seconds
        else:
            raise ValueError('Incorrect parameters: WIND_UNITS in config is not set up correctly.')

    elif var_type == 'precipitation':
        if config_dict['precipitation_units'] == 0:  # mm/day
            pass
        elif config_dict['precipitation_units'] == 1:  # meters/day
            converted_data = np.array(original_data * 1000)
        elif config_dict['precipitation_units'] == 2:  # inches/day
            converted_data = np.array(original_data * 25.4)
        else:
            raise ValueError('Incorrect parameters: PRECIPITATION_UNITS in config is not set up correctly.')

    elif var_type == 'solar_radiation':
        if config_dict['solar_radiation_units'] == 0:  # w/m2
            pass
        elif config_dict['solar_radiation_units'] == 1:  # mj/m2
            # convert MJ to J and divide by seconds in the day
            converted_data = np.array((original_data * 1000000) / 86400)
        elif config_dict['solar_radiation_units'] == 2:  # kw-hr/m2
            # convert kw to w and divide by hours per day
            converted_data = np.array((original_data * 1000) / 24)
        elif config_dict['solar_radiation_units'] == 3:  # langleys
            # equation from https://www.wcc.nrcs.usda.gov/ftpref/wntsc/H&H/GEM/SolarRadConversion.pdf
            converted_data = np.array(original_data * 0.484583)
        else:
            raise ValueError('Incorrect parameters: SOLAR_RADIATION_UNITS in config is not set up correctly.')

    elif var_type == 'vapor_pressure':
        if config_dict['vapor_pressure_units'] == 0:  # kpa
            pass
        elif config_dict['vapor_pressure_units'] == 1:  # pa
            converted_data = np.array(original_data / 1000)
        elif config_dict['vapor_pressure_units'] == 2:  # torr or mmhg
            converted_data = np.array(original_data * 0.133322)
        elif config_dict['vapor_pressure_units'] == 3:  # millibars
            converted_data = np.array(original_data * 0.1)
        elif config_dict['vapor_pressure_units'] == 4:  # atmospheres
            converted_data = np.array(original_data * 101.325)
        else:
            raise ValueError('Incorrect parameters: VAPOR_PRESSURE_UNITS in config is not set up correctly.')

    elif var_type == 'relative_humidity':
        if config_dict['relative_humidity_units'] == 0:  # percentage
            pass
        elif config_dict['relative_humidity_units'] == 1:  # decimal
            converted_data = np.array(original_data * 100.0)
        else:
            raise ValueError('Incorrect parameters: RELATIVE_HUMIDITY_UNITS in config is not set up correctly.')

    else:
        # If an unsupported variable type is passed, raise a value error to point it out.
        raise ValueError('Unsupported variable type {} passed to convert_units function.'.format(var_type))

    return converted_data


def daily_realistic_limits(original_data, log_path, var_type):
    """
        Applies a realistic limit to data to automatically catch and remove bad values that may have resulted
        from sensor malfunctions, sensor degradation, etc. Caught values are replaced by a numpy nan. This function
        assumes all variables are already in metric units

        Args:
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

    warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning for nans in data

    if var_type in ['temperature']:
        limited_data[original_data <= -50] = clip_value  # -50 C is -58 F
        limited_data[original_data >= 60] = clip_value  # 60 C is 140 F
    elif var_type == 'wind_speed':
        limited_data[original_data < 0.1] = clip_value  # Negative wind speed is impossible
        limited_data[original_data >= 35] = clip_value  # 35 m/s is a cat 1 hurricane
    elif var_type == 'precipitation':
        limited_data[original_data < 0] = clip_value  # Negative precipitation is impossible
        limited_data[original_data >= 610] = clip_value  # 610 mm is 2 ft of rain a day
    elif var_type == 'solar_radiation':
        limited_data[original_data <= 5] = clip_value
        limited_data[original_data >= 700] = clip_value
    elif var_type == 'vapor_pressure':
        limited_data[original_data <= 0] = clip_value  # Negative vapor pressure is impossible
        limited_data[original_data >= 8] = clip_value
    elif var_type == 'relative_humidity':
        limited_data[original_data < 2] = clip_value
        limited_data[original_data > 110] = clip_value  # avg relative humidity above 100% is unlikely even with drift
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

    warnings.resetwarnings()  # reset warning filter to default
    return limited_data  # Return the limited data


def remove_isolated_observations(original_var):
    """
        Iterates through provided variable and tries to find any isolated observation, here defined as any observation
        that is surrounded by missing observations, and sets them to nan.

        While this is deleting likely valid data, it is an important step because work is validated visually using bokeh
        plots, which will not display isolated points and we do not want possibly bad values to slip though.

        The actual occurrence of an observation being surrounded by nans should be rare enough that this function has
        little impact.

        Args:
            original_var : 1D numpy array of original variable data

        Returns:
            processed_var : 1D numpy array of variable that has been filtered of all isolated observations.
    """

    data_size = original_var.shape[0]  # number of rows in data
    processed_var = np.empty(data_size) * np.nan

    for i in range(data_size):
        if i == 0 or i == (data_size - 1):  # Special handling for first and last index
            if i == 0:  # First index
                if np.isnan(original_var[i + 1]):
                    # Very first observation is followed by a nan, remove it
                    pass
                else:
                    # First observation is not followed by a nan
                    processed_var[i] = original_var[i]
            else:  # last index
                if np.isnan(original_var[i - 1]):
                    # Very last observation is preceded by a nan, remove it
                    pass
                else:
                    # Last observation is not preceded by a nan
                    processed_var[i] = original_var[i]

        elif np.isnan(original_var[i - 1]) and np.isnan(original_var[i + 1]) and not np.isnan(original_var[i]):
            # Observation is surrounded by nans, remove it.
            pass
        else:
            # Either observation is valid and not surrounded by nans or is itself a nan.
            processed_var[i] = original_var[i]

    return processed_var


def process_variable(config_dict, raw_data, var_name):
    """
        Combines the functions extract_var, convert_units, and daily_realistic_limits to increase readability. First,
        the function extracts individual variables from the raw data, then converts them into the expected metric units,
        sends them through a pass through filter to make sure there are no unrealistic values, and finally filters them
        again to remove all isolated observations that will not display on bokeh plots.

        Args:
            config_dict : dictionary of all config file values
            raw_data : 2D matrix of raw data pulled from .csv/xlsx specified in config file
            var_name : string of text used to signify what variable has been requested.

        Returns:
            processed_var : 1D numpy array of variable that has been extracted, converted, and filtered
            var_col : column of pulled variable, used to track what is provided and what is calculated
    """

    var_name = var_name.lower()

    if var_name == 'maximum_temperature':
        var_col = config_dict['tmax_col']
        var_type = 'temperature'
    elif var_name == 'minimum_temperature':
        var_col = config_dict['tmin_col']
        var_type = 'temperature'
    elif var_name == 'average_temperature':
        var_col = config_dict['tavg_col']
        var_type = 'temperature'
    elif var_name == 'dewpoint_temperature':
        var_col = config_dict['tdew_col']
        var_type = 'temperature'
    elif var_name == 'maximum_relative_humidity':
        var_col = config_dict['rhmax_col']
        var_type = 'relative_humidity'
    elif var_name == 'minimum_relative_humidity':
        var_col = config_dict['rhmin_col']
        var_type = 'relative_humidity'
    elif var_name == 'average_relative_humidity':
        var_col = config_dict['rhavg_col']
        var_type = 'relative_humidity'
    elif var_name == 'vapor_pressure':
        var_col = config_dict['ea_col']
        var_type = 'vapor_pressure'
    elif var_name == 'wind_speed':
        var_col = config_dict['uz_col']
        var_type = 'wind_speed'
    elif var_name == 'precipitation':
        var_col = config_dict['pp_col']
        var_type = 'precipitation'
    elif var_name == 'solar_radiation':
        var_col = config_dict['rs_col']
        var_type = 'solar_radiation'
    else:
        # If an unsupported variable type is passed, raise a value error to point it out.
        raise ValueError('Unsupported variable type {} passed to process_variable function.'.format(var_name))

    original_var = extract_variable(raw_data, var_col)  # Will either return data or an array of nans of expected size
    converted_var = convert_units(config_dict, original_var, var_type)  # converts data to appropriate units
    filtered_var = daily_realistic_limits(converted_var, config_dict['log_file_path'], var_type)  # removed bad vals
    processed_var = remove_isolated_observations(filtered_var)  # returns data with no isolated observations

    return processed_var, var_col


def obtain_data(config_file_path, metadata_file_path=None):
    """
        Uses read_config() to acquire a full dictionary of the config file and then uses the values contained within it
        to direct how data is processed and what variables are obtained.

        If a metadata file is provided, the config file will still be used for data organization, but the metadata will
        be pulled from the metadata file.

        Args:
            config_file_path : string of path to config file, should work with absolute or relative path
            metadata_file_path : string of path to metadata file if provided

        Returns:
            extracted_data : pandas dataframe of entire dataset, with the variables being organized into columns
            col_ser : pandas series of what variables are stored in what columns, used to track which vars are provided
            station_name : string of file, including path, that was provided to dataset
            log_file : string of log file, including path, that was provided to dataset
            station_lat : station latitude in decimal degrees
            station_elev : station elevation in meters
            anemom_height : height of anemometer in meters
            fill_value : value pulled from config file that indicates missing data in output file
            gen_bokeh : boolean flag for if user wants to plot graphs or not
    """

    # Open config file
    validate_file(config_file_path, ['ini'])
    config_dict = read_config(config_file_path)
    print('\nSystem: Successfully opened config file at %s' % config_file_path)

    # Open metadata file
    # If a metadata file is provided we will open it and overwrite values in config_dict with its values
    if metadata_file_path is not None:

        validate_file(metadata_file_path, 'xlsx')  # Validate file to make sure it exists and is the right type
        metadata_df = pd.read_excel(metadata_file_path, sheet_name=0, index_col=0, engine='openpyxl',
                                    keep_default_na=True, na_filter=True, verbose=True)
        print('\nSystem: Successfully opened metadata file at %s' % metadata_file_path)

        # Pull out the metadata for the next file to process
        # also check that the metadata file has outstanding entries to be processed, otherwise raise an error
        processed_rows = metadata_df.processed.ne(1)
        if processed_rows.eq(False).all():
            raise IOError(f'\n\nThe metadata file at \'{metadata_file_path}\' '
                          f'contains no unprocessed (processed == 1) files. \n'
                          f'If you are seeing this before processing any files, make sure the \'processed\' '
                          f'column in the metadata file has been set up with all entries are set to \'0\'.')
        current_row = processed_rows.idxmax() - 1
        metadata_series = metadata_df.iloc[current_row]

        config_dict['data_file_path'] = metadata_series.input_path
        config_dict['station_latitude'] = metadata_series.latitude
        config_dict['station_longitude'] = metadata_series.longitude
        config_dict['station_elevation'] = metadata_series.elev_m
        config_dict['anemometer_height'] = metadata_series.anemom_height_m

        # split file string on extension
        (file_name, station_extension) = os.path.splitext(config_dict['data_file_path'])

        # check to see if file is in a subdirectory in the same folder as the script
        if '/' in file_name:
            (folder_path, delimiter, _station_name) = file_name.rpartition('/')
        elif '\\' in file_name:
            (folder_path, delimiter, _station_name) = file_name.rpartition('\\')
        else:
            folder_path = os.getcwd()

        # Add new keys to config_dict for directory and file information to save files later on
        config_dict['station_name'] = str(metadata_series.id)
        config_dict['file_name'] = file_name
        config_dict['station_extension'] = station_extension
        config_dict['folder_path'] = folder_path

    else:  # No metadata file was provided, use the path info of the data file to construct path variables

        metadata_df = None
        metadata_series = None
        (file_name, station_extension) = os.path.splitext(config_dict['data_file_path'])

        # check to see if file is in a subdirectory or by itself
        if '/' in file_name:
            (folder_path, delimiter, station_name) = file_name.rpartition('/')
        elif '\\' in file_name:
            (folder_path, delimiter, station_name) = file_name.rpartition('\\')
        else:
            station_name = file_name
            folder_path = os.getcwd()

        # Add new keys to config_dict for directory and file information to save files later on
        config_dict['station_name'] = station_name
        config_dict['file_name'] = file_name
        config_dict['station_extension'] = station_extension
        config_dict['folder_path'] = folder_path

    # Check lines_of_header value, if 0 change it to NONE, if nonzero minus it by one
    if config_dict['lines_of_header'] == 0:
        config_dict['lines_of_header'] = None
    else:
        config_dict['lines_of_header'] = config_dict['lines_of_header'] - 1

    # Open data file
    validate_file(config_dict['data_file_path'], ['csv', 'xls', 'xlsx'])
    if station_extension == '.csv':  # csv file provided
        raw_data = pd.read_csv(config_dict['data_file_path'], delimiter=',', header=config_dict['lines_of_header'],
                               index_col=None, engine='python', skipfooter=config_dict['lines_of_footer'],
                               na_values=config_dict['missing_input_value'], keep_default_na=True,
                               na_filter=True, verbose=True, skip_blank_lines=True)

    elif station_extension == '.xlsx':
        raw_data = pd.read_excel(config_dict['data_file_path'], sheet_name=0, header=config_dict['lines_of_header'],
                                 index_col=None, engine='openpyxl', skipfooter=config_dict['lines_of_footer'],
                                 na_values=config_dict['missing_input_value'], keep_default_na=True,
                                 na_filter=True, verbose=True)

    elif station_extension == '.xls':
        raw_data = pd.read_excel(config_dict['data_file_path'], sheet_name=0, header=config_dict['lines_of_header'],
                                 index_col=None, engine='xlrd', skipfooter=config_dict['lines_of_footer'],
                                 na_values=config_dict['missing_input_value'], keep_default_na=True,
                                 na_filter=True, verbose=True)

    else:
        # This script is only handles csv and Excel files. Validate_file() already catches this case
        raise IOError('\n\nProvided file was of type \'{}\' but script was expecting type \'{}\'.'
                      .format(station_extension, ['csv', 'xls', 'xlsx']))

    print('\nSystem: Successfully opened data file at %s' % config_dict['data_file_path'])

    # Handle any for network-specific oddities that may have slipped through
    raw_data = raw_data.replace(to_replace='NO RECORD   ', value=np.nan)  # catch for whitespaces on agriment

    # check for the existence of 'correction_files' folder and if not present make one
    if not os.path.exists(folder_path + '/correction_files'):
        os.makedirs(folder_path + '/correction_files')
        os.makedirs(folder_path + '/correction_files/before_graphs/')
        os.makedirs(folder_path + '/correction_files/after_graphs/')
        os.makedirs(folder_path + '/correction_files/histograms/')
        os.makedirs(folder_path + '/correction_files/log_files/')
        os.makedirs(folder_path + '/correction_files/output_data/')
    else:
        pass

    # Create log file for this new data file
    config_dict['log_file_path'] = config_dict['folder_path'] + \
        '/correction_files/log_files/' + config_dict['station_name'] + '_changes_log' + '.txt'
    log.basicConfig()
    logger = open(config_dict['log_file_path'], 'w')
    logger.write('The raw data for %s has been successfully read in at %s. \n \n' %
                 (config_dict['station_name'], pd.Timestamp.now().strftime('%Y-%m-%d %X')))
    logger.close()
    print('\nSystem: Successfully created log file at %s.' % config_dict['log_file_path'])

    # Date handling, figures out the date format and extracts from string if needed
    if config_dict['date_format'] == 1:
        # Date is provided as a string, expected format is MM/DD/YYYY, time can be included as well.
        if config_dict['string_date_col'] != -1:
            data_date = np.array(raw_data.iloc[:, config_dict['string_date_col']])
            dt_date = pd.to_datetime(data_date, errors='raise')
            data_day = np.array(dt_date.day.astype('int'))
            data_month = np.array(dt_date.month.astype('int'))
            data_year = np.array(dt_date.year.astype('int'))
        else:
            # date format was provided as a string date but no string date was given
            raise ValueError('Date format parameter indicated a string date but none was provided')

    elif config_dict['date_format'] == 2:

        if config_dict['month_col'] != -1 and config_dict['day_col'] != -1 and config_dict['year_col'] != -1:
            data_month = np.array(raw_data.iloc[:, config_dict['month_col']].astype('int'))
            data_day = np.array(raw_data.iloc[:, config_dict['day_col']].astype('int'))
            data_year = np.array(raw_data.iloc[:, config_dict['year_col']].astype('int'))
        else:
            # date format was provided as separate columns but some were missing
            raise ValueError('Date format parameter indicated separate Y/M/D columns but some or all were missing.')

    elif config_dict['date_format'] == 3:
        # Date is pre-split between year column and DOY column

        if config_dict['day_of_year_col'] != -1 and config_dict['year_col'] != -1:
            data_doy = np.array(raw_data.iloc[:, config_dict['day_of_year_col']].astype('int'))
            data_year = np.array(raw_data.iloc[:, config_dict['year_col']].astype('int'))
        else:
            # date format was provided as separate year and doy columns but some were missing
            raise ValueError('Date format parameter indicated year and DOY columns but some or all were missing.')

        dt_date = pd.to_datetime(data_year * 1000 + data_doy, format='%Y%j', errors='raise')
        data_day = np.array(dt_date.day.astype('int'))
        data_month = np.array(dt_date.month.astype('int'))
        data_year = np.array(dt_date.year.astype('int'))

    else:
        # Script cannot function without a time variable
        raise ValueError('Parameter error: date_format is set to an unexpected value.')

    #########################
    # Variable processing
    # Imports all weather variables, converts them into the correct units, and filters them to remove impossible values

    (data_tmax, tmax_col) = process_variable(config_dict, raw_data, 'maximum_temperature')
    (data_tmin, tmin_col) = process_variable(config_dict, raw_data, 'minimum_temperature')
    (data_tavg, tavg_col) = process_variable(config_dict, raw_data, 'average_temperature')
    (data_tdew, tdew_col) = process_variable(config_dict, raw_data, 'dewpoint_temperature')
    (data_ea, ea_col) = process_variable(config_dict, raw_data, 'vapor_pressure')
    (data_rhmax, rhmax_col) = process_variable(config_dict, raw_data, 'maximum_relative_humidity')
    (data_rhmin, rhmin_col) = process_variable(config_dict, raw_data, 'minimum_relative_humidity')
    (data_rhavg, rhavg_col) = process_variable(config_dict, raw_data, 'average_relative_humidity')
    (data_rs, rs_col) = process_variable(config_dict, raw_data, 'solar_radiation')
    (data_ws, ws_col) = process_variable(config_dict, raw_data, 'wind_speed')
    (data_precip, precip_col) = process_variable(config_dict, raw_data, 'precipitation')

    # HPRCC data reports '0' for missing observations as well as a text column, but this script doesn't interpret text
    # columns, so instead we see if both tmax and tmin have the same value (0, or -17.7778 depending on units) and if so
    # mark that row as missing
    # realistically tmax should never equal tmin, so this is an okay check to have in general
    for i in range(len(data_tmax)):
        if data_tmax[i] == data_tmin[i]:
            data_tmax[i] = np.nan
            data_tmin[i] = np.nan
            data_tavg[i] = np.nan
            data_tdew[i] = np.nan
            data_ea[i] = np.nan
            data_rhmax[i] = np.nan
            data_rhmin[i] = np.nan
            data_rhavg[i] = np.nan
            data_rs[i] = np.nan
            data_ws[i] = np.nan
            data_precip[i] = np.nan
        else:
            pass

    #########################
    # Dataframe Construction
    # In this section we convert the individual numpy arrays into a pandas dataframe to accomplish several goals:
    # 1. Make use of the pandas reindexing function to cover literal gaps in the dataset (not just missing values)
    # 2. Resample data to remove any duplicate records (same day appears twice in dataset, first instance is kept)
    # 3. Cleanly pass extracted data to the main script function

    # Create Datetime dataframe for reindexing
    datetime_df = pd.DataFrame({'year': data_year, 'month': data_month, 'day': data_day})
    datetime_df = pd.to_datetime(datetime_df)

    # Create a series of all dates in time series
    date_reindex = pd.date_range(datetime_df.iloc[0], datetime_df.iloc[-1])

    reindexing_additions = np.setdiff1d(np.array(date_reindex), np.array(datetime_df), assume_unique=False)

    logger = open(config_dict['log_file_path'], 'w')
    logger.write('The raw data file had %s missing date entries from its time record. \n \n' %
                 reindexing_additions.size)
    logger.close()

    print('\nSystem: The input data file had %s missing dates in its time record.' % reindexing_additions.size)

    # Create dataframe of data
    data_df = pd.DataFrame({'year': data_year, 'month': data_month,
                            'day': data_day, 'tavg': data_tavg, 'tmax': data_tmax, 'tmin': data_tmin,
                            'tdew': data_tdew, 'ea': data_ea, 'rhavg': data_rhavg, 'rhmax': data_rhmax,
                            'rhmin': data_rhmin, 'rs': data_rs, 'ws': data_ws, 'precip': data_precip},
                           index=datetime_df)

    # Create dataframe of column indices for weather variable, to track which ones were provided vs calculated
    col_ser = pd.Series({'tmax': tmax_col, 'tmin': tmin_col, 'tavg': tavg_col, 'tdew': tdew_col, 'ea': ea_col,
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

    return data_df, col_ser, metadata_df, metadata_series, config_dict


# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
