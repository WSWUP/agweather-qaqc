from bokeh.layouts import gridplot
from bokeh.plotting import output_file, reset_output, save
import datetime as dt
import numpy as np
import pandas as pd
from qaqc_modules import data_functions, input_functions, plotting_functions, qaqc_functions
from refet.calcs import _wind_height_adjust

#########################
# Initial setup
# TODO: finish implementing log file within this script
# TODO: add fill function for all missing temp data and adjust fill vars accordingly
# TODO: change uniform to normal
# TODO: functionalize qaqc_functions and add comment text
# TODO: investigate changing bokehs to functions
# TODO: this script cannot handle only tavg, its only setup for max/min
# TODO: contemplate just keeping everything as a pandas dataframe
# TODO: Add optimization for TR_Rs to each place it appears (2)
#  rs_tr reg is saved as both orig and opt in output file at the minute
# TODO: look into where "reset_output()" should
# TODO: put fill functions from scratch file back into this, figure out where
# TODO: simply fill tracking section with a function
# TODO: decide if tr_rs should fill before or after solar radiation correction
# TODO: fill temperature data totally
# TODO: find a way to fill wind so we have a complete record of et
# TODO: tracking changes to opt_rs_tr is meaningless because its randomly generated, should i track rs_tr as well?
#    Maybe solution should be comparing original rs_tr with orignal coefficients vs optimized corrected?

print("\nSystem: Starting data correction script.")
config_path = 'config.ini'  # Hardcoded for now, eventually will create function to pull config path from excel file
mc_iterations = 50000  # Hardcoded, consider adding to ini?
mc_loop = 1

#########################
# Obtaining initial data
(data_df, column_df, station_name, log_file, station_lat, station_elev, ws_anemometer_height,
 missing_fill_value, script_mode, generate_bokeh) = input_functions.obtain_data(config_path)

print("\nSystem: Raw data successfully extracted from station file.")

# Extract individual variables from data frame back into to numpy arrays.
data_year = np.array(data_df.year)
data_month = np.array(data_df.month)
data_day = np.array(data_df.day)
data_tavg = np.array(data_df.tavg)
data_tmax = np.array(data_df.tmax)
data_tmin = np.array(data_df.tmin)
data_tdew = np.array(data_df.tdew)
data_ea = np.array(data_df.ea)
data_rhavg = np.array(data_df.rhavg)
data_rhmax = np.array(data_df.rhmax)
data_rhmin = np.array(data_df.rhmin)
data_rs = np.array(data_df.rs)
data_ws = np.array(data_df.ws)
data_precip = np.array(data_df.precip)

#########################
# Calculating secondary variables
print("\nSystem: Now calculating secondary variables based on data provided.")
data_length = data_year.shape[0]
station_pressure = 101.3 * (((293 - (0.0065 * station_elev)) / 293) ** 5.26)  # units kPa, EQ 3 in ASCE RefET manual

# Calculate DOY from Y/M/D values
data_doy = []
for i in range(data_length):
    data_doy.append(dt.date(data_year[i], data_month[i], data_day[i]).strftime("%j"))  # list of string DOY values

data_doy = np.array(list(map(int, data_doy)))  # Converts list of string values into ints and saves as numpy array

# Figure out which humidity variables are provided and calculate Ea and TDew if needed
(data_ea, data_tdew) = data_functions.calc_humidity_variables(data_tmax, data_tmin, data_tavg, data_ea,
                                                              column_df.ea, data_tdew, column_df.tdew, data_rhmax,
                                                              column_df.rhmax, data_rhmin, column_df.rhmin,
                                                              data_rhavg, column_df.rhavg)

# Calculates secondary temperature values and mean monthly counterparts
(delta_t, mm_delta_t, k_not, mm_k_not, mm_tmin, mm_tdew) = data_functions.\
    calc_temperature_variables(data_month, data_tmax, data_tmin, data_tdew)

# Calculates rso and grass/alfalfa reference evapotranspiration from refet package
# TODO: consider silencing RuntimeWarnings over invalid values (nans)
(rso, mm_rs, eto, etr, mm_eto, mm_etr) = data_functions.\
    calc_rso_and_refet(station_lat, station_elev, ws_anemometer_height, data_doy, data_month,
                       data_tmax, data_tmin, data_ea, data_ws, data_rs)

#########################
# Back up original data
# Original data will be saved to output file
# Values are also used to generate delta values of corrected data - original data
original_df = data_df.copy(deep=True)  # Create an unlinked copy of read-in values dataframe
original_df['rso'] = rso
original_df['etr'] = etr
original_df['eto'] = eto

#########################
# Correcting Data
# Loop where user selects an option, corrects it, script recalculates, and then loops.
# If user opts to not correct data (sets script_mode = 0), then skips this section and just generates composite plot
print("\nSystem: Now beginning correction on data.")

# Create variables that will be used by bokeh plot and correction functions
dt_array = []
for i in range(data_length):
    dt_array.append(dt.datetime(data_year[i], data_month[i], data_day[i]))
dt_array = np.array(dt_array, dtype=np.datetime64)
mm_dt_array = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
data_null = np.empty(data_length) * np.nan

# Create arrays that will track which values have been filled (replace missing data) by the script
fill_ea = np.zeros(data_length)
fill_tdew = np.zeros(data_length)
fill_rs = np.zeros(data_length)

# Begin loop for correcting variables
while script_mode == 1:
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
    choice_loop = 1
    while choice_loop:
        if 1 <= user <= 7:
            if column_df.ea == -1 and column_df.rhmax == -1 and column_df.rhmin == -1 and column_df.rhavg == -1:
                # User selected option to correct humidity when the only var provided is tdew
                print('\nOnly TDew was provided as a humidity variable, which is corrected under option 2.')
                user = int(input('Specify which variable you would like to correct: '))
            else:
                choice_loop = 0
        else:
            print('\nPlease enter a valid option.')
            user = int(input('Specify which variable you would like to correct: '))

    ##########
    # Correcting individual variables based on user choice
    # Correcting Max/Min Temperature data
    if user == 1:
        (data_tmax, data_tmin) = qaqc_functions.correction(station_name, log_file, data_tmax, 'TMax', data_tmin,
                                                           'TMin', dt_array, data_month, data_year, 1)
    # Correcting Min/Dew Temperature data
    elif user == 2:
        (data_tmin, data_tdew) = qaqc_functions.correction(station_name, log_file, data_tmin, 'TMin', data_tdew,
                                                           'TDew', dt_array, data_month, data_year, 1)
    # Correcting Windspeed
    elif user == 3:
        (data_ws, data_null) = qaqc_functions.correction(station_name, log_file, data_ws, 'Ws', data_null,
                                                         'NONE', dt_array, data_month, data_year, 4)
    # Correcting Solar radiation
    elif user == 4:
        (data_rs, data_null) = qaqc_functions.correction(station_name, log_file, data_rs, 'Rs', rso,
                                                         'Rso', dt_array, data_month, data_year, 3)
    # Correcting Humidity Variable
    elif user == 5:
        # Variables passed depends on what variables were provided
        if column_df.ea != -1:
            # Vapor Pressure exists
            (data_ea, data_null) = qaqc_functions.correction(station_name, log_file, data_ea, 'Vapor Pressure',
                                                             data_null, 'NONE', dt_array, data_month, data_year, 4)

        elif column_df.ea == -1 and column_df.rhmax != -1 and column_df.rhmin != -1:
            # No vapor pressure but have rhmax and min
            (data_rhmax, data_rhmin) = qaqc_functions.correction(station_name, log_file, data_rhmax, 'RHMax',
                                                                 data_rhmin, 'RHMin', dt_array, data_month,
                                                                 data_year, 2)

        elif column_df.ea == -1 and column_df.rhmax == -1 and column_df.rhmin == -1 and column_df.rhavg != -1:
            # Only have RHavg
            (data_rhavg, data_null) = qaqc_functions.correction(station_name, log_file, data_rhavg, 'RHAvg',
                                                                data_null, 'NONE', dt_array, data_month, data_year, 4)
        else:
            # If an unsupported combination of humidity variables is present, raise a value error.
            raise ValueError('Humidity correction section encountered an unexpected combination of humidity inputs.')

    # Correcting Precipitation
    elif user == 6:
        (data_precip, data_null) = qaqc_functions.correction(station_name, log_file, data_precip, 'Precip', data_null,
                                                             'NONE', dt_array, data_month, data_year, 4)
    else:
        # user quits, exit out of loop
        print('\nSystem: Now finishing up corrections.')
        break  # Break here because all recalculations were done at the end of the last loop iteration

    ##########
    # Now that a variable has been corrected, recalculate all relevant secondary variables

    if user == 1 or user == 2 or user == 5:
        # Figure out which humidity variables are provided and recalculate Ea and TDew if needed
        # This function is safe to use after correcting because it tracks what variable was provided by the data file
        # and recalculates appropriately. It doesn't overwrite provided variables with calculated versions.
        # Ex. if only TDew is provided, it recalculates ea while returning original provided tdew
        (data_ea, data_tdew) = data_functions.calc_humidity_variables(data_tmax, data_tmin, data_tavg, data_ea,
                                                                      column_df.ea, data_tdew, column_df.tdew,
                                                                      data_rhmax, column_df.rhmax, data_rhmin,
                                                                      column_df.rhmin, data_rhavg, column_df.rhavg)

        # Recalculates secondary temperature values and mean monthly counterparts
        (delta_t, mm_delta_t, k_not, mm_k_not, mm_tmin, mm_tdew) = data_functions. \
            calc_temperature_variables(data_month, data_tmax, data_tmin, data_tdew)

        #####
        # Fill in any missing tdew data with tmin - k0 curve.
        # Once TDew is filled, if that filled index is also empty for ea, then we use filled tdew to calculate ea
        # If ea is provided and NOT empty at that index we do nothing to avoid overwriting actual data with filled data
        # and the now filled TDew sections are used to calculate ea for those filled indices.
        # Nothing occurs if this fill code is run a second time because vars are already filled unless
        # correction methods throw out data.
        for i in range(data_length):
            if np.isnan(data_tdew[i]):
                data_tdew[i] = data_tmin[i] - mm_k_not[data_month[i] - 1]
                fill_tdew[i] = data_tdew[i]

                # TODO: Confirm on when Ea should be filled, before or after ea is actually corrected
                if column_df.ea == -1 or (column_df.ea != -1 and not np.isnan(data_ea[i])):
                    # Either Ea not provided, OR Ea is provided and this index is empty and can be filled
                    data_ea[i] = (0.6108 * np.exp((17.27 * data_tdew[i]) / (data_tdew[i] + 237.3)))
                    fill_ea[i] = data_ea[i]
                else:
                    # Ea is provided and the index is not empty, do nothing to avoid overwriting actual data
                    pass
            else:
                # If TDew isn't empty then nothing is required to be done.
                pass
    else:
        pass

    # Recalculates rso and grass/alfalfa reference evapotranspiration from refet package
    (rso, mm_rs, eto, etr, mm_eto, mm_etr) = data_functions. \
        calc_rso_and_refet(station_lat, station_elev, ws_anemometer_height, data_doy, data_month,
                           data_tmax, data_tmin, data_ea, data_ws, data_rs)

#########################
# Final calculations
# Now that corrections are done, calculate thornton-running solar radiation, use it to fill data_rs
# Then finally recalculate reference evapotranspiration with the filled data_rs
# TODO PUT A gate here so this doesnt happen (or at least part of it doesnt) if user doesn't correct data?
for i in range(mc_loop):
    (orig_rs_tr, mm_orig_rs_tr, opt_rs_tr, mm_opt_rs_tr) = data_functions.\
        calc_org_and_opt_rs_tr(mc_iterations, log_file, data_month, delta_t, mm_delta_t, data_rs, rso)

# loop to fill data_rs
for i in range(data_length):
    if np.isnan(data_rs[i]):
        data_rs[i] = opt_rs_tr[i]
        fill_rs[i] = opt_rs_tr[i]
    else:
        # If rs isn't empty then nothing is required to be done.
        pass

# Recalculate eto and etr one final time
(rso, mm_rs, eto, etr, mm_eto, mm_etr) = data_functions. \
    calc_rso_and_refet(station_lat, station_elev, ws_anemometer_height, data_doy,
                       data_month, data_tmax, data_tmin, data_ea, data_ws, data_rs)


#########################
# Generate bokeh composite plot
# Creates one large plot featuring all variables as subplots, used to get a concise overview of the full dataset
# If user opts to not correct data (sets script_mode = 0), then this plots data before correction
# If user does correct data, then this plots data after correction
print("\nSystem: Now creating composite bokeh graph.")

# TODO: This warning -  DeprecationWarning: Using or importing the ABCs from 'collections' instead of from
#   'collections.abc' is deprecated, and in 3.8 it will stop working - is caused by code within bokeh package,
#   and is being worked on as of 2/2/19, keep track of it and update when they fix it.
if generate_bokeh:  # Flag to create graphs or not

    x_size = 500
    y_size = 350

    if script_mode == 0:
        output_file(station_name + "_before_corrections_composite_graph.html")
    elif script_mode == 1:
        output_file(station_name + "_after_corrections_composite_graph.html")
    else:
        # Incorrect setup of script mode variable, raise an error
        raise ValueError('Incorrect parameters: script mode is not set to a valid option.')

    # Temperature Maximum and Minimum Plot
    plot_tmax_tmin = plotting_functions.create_plot(x_size, y_size, dt_array, data_tmax, 'TMax', 'red', data_tmin,
                                                    'TMin', 'blue', 'Celsius')
    # Temperature Minimum and Dewpoint Plot
    plot_tmin_tdew = plotting_functions.create_plot(x_size, y_size, dt_array, data_tmin, 'TMin', 'blue', data_tdew,
                                                    'TDew', 'black', 'Celsius', plot_tmax_tmin)

    # Subplot 3 changes based on what variables are provided
    if column_df.ea != -1:  # Vapor pressure was provided
        plot_humid = plotting_functions.create_plot(x_size, y_size, dt_array, data_ea, 'Ea', 'black', data_null, 'null',
                                                    'black', 'kPa', plot_tmax_tmin)
    elif column_df.ea == -1 and column_df.tdew != -1:  # Tdew was provided, show calculated vapor pressure
        plot_humid = plotting_functions.create_plot(x_size, y_size, dt_array, data_ea, 'Calculated Ea', 'black',
                                                    data_null, 'null', 'black', 'kPa', plot_tmax_tmin)
    elif column_df.ea == -1 and column_df.tdew == -1 and column_df.rhmax != -1 and column_df.rhmin != -1:  # RH max/min
        plot_humid = plotting_functions.create_plot(x_size, y_size, dt_array, data_rhmax, 'RHMax', 'blue', data_rhmin,
                                                    'RHMin', 'red', 'Percentage (%)', plot_tmax_tmin)
    elif column_df.ea == -1 and column_df.tdew == -1 and column_df.rhmax == -1 and column_df.rhavg != -1:  # RHavg only
        plot_humid = plotting_functions.create_plot(x_size, y_size, dt_array, data_rhavg, 'RHAvg', 'blue', data_null,
                                                    'null', 'black', 'Percentage (%)', plot_tmax_tmin)
    else:
        # If an unsupported combination of humidity variables is present, raise a value error.
        raise ValueError('Bokeh figure generation encountered an unexpected combination of humidity inputs.')

    # Mean Monthly Temperature Minimum and Dewpoint
    plot_mm_tmin_tdew = plotting_functions.create_plot(x_size, y_size, mm_dt_array, mm_tmin, 'MM TMin', 'blue', mm_tdew,
                                                       'MM TDew', 'black', 'Celsius')

    # Mean Monthly k0 curve (Tmin-Tdew)
    plot_mm_k_not = plotting_functions.create_plot(x_size, y_size, mm_dt_array, mm_k_not, 'k0 Curve', 'black',
                                                   data_null, 'null', 'black', 'Celsius', plot_mm_tmin_tdew)

    # Solar radiation and clear sky solar radiation
    plot_rs_rso = plotting_functions.create_plot(x_size, y_size, dt_array, rso, 'Clear-Sky Rs', 'black', data_rs, 'Rs',
                                                 'red', 'w/m2', plot_tmax_tmin)

    # Optimized mean monthly Thornton-Running solar radiation and Mean Monthly solar radiation
    plot_mm_opt_rs_tr = plotting_functions.create_plot(x_size, y_size, mm_dt_array, mm_rs, 'MM Rs', 'red', mm_opt_rs_tr,
                                                       'Optimized MM TR Rs', 'blue', 'w/m2', plot_mm_tmin_tdew)

    # Optimized mean monthly Thornton-Running solar radiation and Mean Monthly solar radiation
    plot_mm_orig_rs_tr = plotting_functions.create_plot(x_size, y_size, mm_dt_array, mm_rs, 'MM Rs', 'red',
                                                        mm_orig_rs_tr, 'Original MM TR Rs', 'blue', 'w/m2',
                                                        plot_mm_tmin_tdew)

    # Windspeed
    plot_ws = plotting_functions.create_plot(x_size, y_size, dt_array, data_ws, 'Wind Speed', 'black', data_null,
                                             'null', 'black', 'm/s', plot_tmax_tmin)
    # Precipitation
    plot_precip = plotting_functions.create_plot(x_size, y_size, dt_array, data_precip, 'Precipitation', 'black',
                                                 data_null, 'null', 'black', 'kPa', plot_tmax_tmin)

    if column_df.rhmax != -1 and column_df.rhmin != -1 and column_df.ea != -1:
        # If both ea and rhmax/rhmin are provided, generate a supplementary rhmax/min graph and save
        supplemental_rh_plot = plotting_functions.create_plot(x_size, y_size, dt_array, data_rhmax, 'RHMax', 'blue',
                                                              data_rhmin, 'RHMin', 'red', 'Percentage (%)',
                                                              plot_tmax_tmin)

        fig = gridplot([[plot_tmax_tmin, plot_tmin_tdew, plot_humid],
                        [plot_mm_tmin_tdew, plot_mm_k_not, supplemental_rh_plot],
                        [plot_rs_rso, plot_ws, plot_precip],
                        [plot_mm_opt_rs_tr, plot_mm_orig_rs_tr]], toolbar_location="left")
        save(fig)
    else:
        # If there is no 10th plot to generate, save the regular 9
        fig = gridplot([[plot_tmax_tmin, plot_tmin_tdew, plot_humid],
                        [plot_mm_tmin_tdew, plot_mm_k_not, plot_rs_rso],
                        [plot_ws, plot_precip, plot_mm_opt_rs_tr]
                        [plot_mm_orig_rs_tr]], toolbar_location="left")
        save(fig)

    print("\nSystem: Composite bokeh graph has been generated.")

#########################
# Generate output file
# Create any final variables, then create panda dataframes to save all the data
# Includes the following sheets:
#     Corrected Data : Actual corrected values
#     Delta : Magnitude of difference between original data and corrected data
#     Filled Data : Tracks which data points have been filled by script generated values instead of being provided
# Data that is provided and subsequently corrected by the script do not count as filled values.
print("\nSystem: Saving corrected data to .xslx file.")

# Create any individually-requested output data
ws_2m = _wind_height_adjust(uz=data_ws, zw=ws_anemometer_height)

# Create fill numpy arrays to show when data was filled
fill_tavg = np.zeros(data_length)
fill_tmax = np.zeros(data_length)
fill_tmin = np.zeros(data_length)
for i in range(data_length):
    # TAvg
    if (original_df.tavg[i] == data_tavg[i]) or (np.isnan(original_df.tavg[i]) and np.isnan(data_tavg[i])):
        # Nothing is required to be done
        pass
    else:
        fill_tavg[i] = data_tavg[i]
    # TMax
    if (original_df.tmax[i] == data_tmax[i]) or (np.isnan(original_df.tmax[i]) and np.isnan(data_tmax[i])):
        # Nothing is required to be done
        pass
    else:
        fill_tmax[i] = data_tmax[i]
    # TMin
    if (original_df.tmin[i] == data_tmin[i]) or (np.isnan(original_df.tmin[i]) and np.isnan(data_tmin[i])):
        # Nothing is required to be done
        pass
    else:
        fill_tmin[i] = data_tmin[i]

# Create corrected-original delta numpy arrays
diff_tavg = np.array(data_tavg - original_df.tavg)
diff_tmax = np.array(data_tmax - original_df.tmax)
diff_tmin = np.array(data_tmin - original_df.tmin)
diff_tdew = np.array(data_tdew - original_df.tdew)
diff_ea = np.array(data_ea - original_df.ea)
diff_rhavg = np.array(data_rhavg - original_df.rhavg)
diff_rhmax = np.array(data_rhmax - original_df.rhmax)
diff_rhmin = np.array(data_rhmin - original_df.rhmin)
diff_rs = np.array(data_rs - original_df.rs)
diff_rs_tr = np.array(opt_rs_tr - orig_rs_tr)
diff_rso = np.array(rso - original_df.rso)
diff_ws = np.array(data_ws - original_df.ws)
diff_precip = np.array(data_precip - original_df.precip)
diff_etr = np.array(etr - original_df.etr)
diff_eto = np.array(eto - original_df.eto)

# Create datetime for output dataframe
datetime_df = pd.DataFrame({'year': data_year, 'month': data_month, 'day': data_day})
datetime_df = pd.to_datetime(datetime_df[['month', 'day', 'year']])

# Create output dataframe
output_df = pd.DataFrame({'date': datetime_df, 'year': data_year, 'month': data_month, 'day': data_day,
                          'TAvg (C)': data_tavg, 'TMax (C)': data_tmax, 'TMin (C)': data_tmin, 'TDew (C)': data_tdew,
                          'Vapor Pres (kPa)': data_ea, 'RHAvg (%)': data_rhavg, 'RHMax (%)': data_rhmax,
                          'RHMin (%)': data_rhmin, 'Rs (w/m2)': data_rs, 'Opt_Rs_TR (w/m2)': opt_rs_tr,
                          'Rso (w/m2)': rso, 'Windspeed (m/s)': data_ws, 'Precip (mm)': data_precip,
                          'ETr (mm)': etr, 'ETo (mm)': eto, 'ws_2m (m/s)': ws_2m},
                         index=datetime_df)

# Creating difference dataframe to track amount of correction
delta_df = pd.DataFrame({'date': datetime_df, 'year': data_year, 'month': data_month, 'day': data_day,
                         'TAvg (C)': diff_tavg, 'TMax (C)': diff_tmax, 'TMin (C)': diff_tmin, 'TDew (C)': diff_tdew,
                         'Vapor Pres (kPa)': diff_ea, 'RHAvg (%)': diff_rhavg, 'RHMax (%)': diff_rhmax,
                         'RHMin (%)': diff_rhmin, 'Rs (w/m2)': diff_rs, 'Opt - Orig Rs_TR (w/m2)': diff_rs_tr,
                         'Rso (w/m2)': diff_rso, 'Windspeed (m/s)': diff_ws, 'Precip (mm)': diff_precip,
                         'ETr (mm)': diff_etr, 'ETo (mm)': diff_eto}, index=datetime_df)

# Creating a fill dataframe that tracks where missing data was filled in
fill_df = pd.DataFrame({'date': datetime_df, 'year': data_year, 'month': data_month, 'day': data_day,
                        'TAvg (C)': fill_tavg, 'TMax (C)': fill_tmax, 'TMin (C)': fill_tmin,
                        'TDew (C)': fill_tdew, 'Vapor Pres (kPa)': fill_ea}, index=datetime_df)

# Open up pandas excel writer
output_writer = pd.ExcelWriter(station_name + "_output" + ".xlsx", engine='xlsxwriter')
# Convert data frames to xlsxwriter excel objects
output_df.to_excel(output_writer, sheet_name='Corrected Data', na_rep=missing_fill_value)
delta_df.to_excel(output_writer, sheet_name='Delta (Corr - Orig)', na_rep=missing_fill_value)
fill_df.to_excel(output_writer, sheet_name='Filled Data', na_rep=missing_fill_value)
# Save output file
output_writer.save()

print("\nSystem: Ending script and closing log file.")

logger = open(log_file, 'a')
logger.write('The file has been successfully processed and output files saved at %s. \n' % dt.datetime.now().strftime(
                                                                                           "%Y-%m-%d %H:%M:%S"))
logger.close()
