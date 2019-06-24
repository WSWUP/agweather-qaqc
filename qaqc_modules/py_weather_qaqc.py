from bokeh.layouts import gridplot
from bokeh.plotting import output_file, reset_output, save
import datetime as dt
import numpy as np
import pandas as pd
from math import ceil
from qaqc_modules import data_functions, input_functions, plotting_functions, qaqc_functions
from refet.calcs import _wind_height_adjust


class WeatherQAQC:

    config_path = 'config.ini'
    metadata_path = None
    station_line = None
    gridplot_columns = 1

    def __init__(self, config_file_path='config.ini', metadata_file_path=None, line_number=None, column_number=1):
        self.config_path = config_file_path
        self.metadata_path = metadata_file_path
        self.station_line = line_number
        self.gridplot_columns = column_number

    #########################
    # Obtaining initial data
    (data_df, column_df, station_name, log_file, station_lat, station_elev, ws_anemometer_height, missing_fill_value,
     script_mode, auto_mode, generate_bokeh) = input_functions.obtain_data(config_path)

    if script_mode == 1:  # correcting data
        mc_iterations = 1000  # Number of iters for MC simulation of thornton running solar radiation generation
    else:
        mc_iterations = 50  # if we're not correcting data then only do a few iterations to save time

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
    np.warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning for nans in data
    (rso, mm_rs, eto, etr, mm_eto, mm_etr) = data_functions.\
        calc_rso_and_refet(station_lat, station_elev, ws_anemometer_height, data_doy, data_month,
                           data_tmax, data_tmin, data_ea, data_ws, data_rs)
    np.warnings.resetwarnings()  # reset warning filter to default

    #########################
    # Back up original data
    # Original data will be saved to output file
    # Values are also used to generate delta values of corrected data - original data
    original_df = data_df.copy(deep=True)  # Create an unlinked copy of read-in values dataframe
    original_df['rso'] = rso
    original_df['etr'] = etr
    original_df['eto'] = eto

    #########################
    # Histograms of original data
    # Generates composite plot of specific variables before correction
    # We fill these variables by sampling a normal distribution, so we use this plot mainly as evidence for that.
    if generate_bokeh:
        ws_hist = plotting_functions.histogram_plot(data_ws[~np.isnan(data_ws)], 'Windspeed', 'black', 'm/s')
        tmax_hist = plotting_functions.histogram_plot(data_tmax[~np.isnan(data_tmax)], 'TMax', 'red', 'degrees C')
        tmin_hist = plotting_functions.histogram_plot(data_tmin[~np.isnan(data_tmin)], 'TMin', 'blue', 'degrees C')
        k_not_hist = plotting_functions.histogram_plot(k_not[~np.isnan(k_not)], 'Ko', 'black', 'degrees C')

        output_file(station_name + '_histograms.html', title=station_name + ' histograms')
        save(gridplot([ws_hist, tmax_hist, tmin_hist, k_not_hist], ncols=2, plot_width=400, plot_height=400,
                      toolbar_location=None))

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
    fill_tmax = np.zeros(data_length)
    fill_tmin = np.zeros(data_length)
    fill_ea = np.zeros(data_length)
    fill_tdew = np.zeros(data_length)
    fill_rs = np.zeros(data_length)
    fill_ws = np.zeros(data_length)

    # Begin loop for correcting variables
    while script_mode == 1:
        reset_output()  # clears bokeh output, prevents ballooning file sizes
        print('\nPlease select which of the following variables you want to correct'
              '\n   Enter 1 for TMax and TMin.'
              '\n   Enter 2 for TMin and TDew.'
              '\n   Enter 3 for Windspeed.'
              '\n   Enter 4 for Precipitation.'
              '\n   Enter 5 for Rs.'
              '\n   Enter 6 for Humidity Measurements (Vapor Pressure, RHMax and RHmin, or RHAvg.)'
              '\n   Enter 7 to stop applying corrections.'
              )

        user = int(input("\nEnter your selection: "))
        choice_loop = 1
        while choice_loop:
            if 1 <= user <= 7:
                if user == 6 and \
                        (column_df.ea == -1 and column_df.rhmax == -1 and
                         column_df.rhmin == -1 and column_df.rhavg == -1):
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
            (data_tmax, data_tmin) = qaqc_functions.correction(station_name, log_file, data_tmax, data_tmin, dt_array,
                                                               data_month, data_year, 1)
        # Correcting Min/Dew Temperature data
        elif user == 2:
            (data_tmin, data_tdew) = qaqc_functions.correction(station_name, log_file, data_tmin, data_tdew, dt_array,
                                                               data_month, data_year, 2)
        # Correcting Windspeed
        elif user == 3:
            (data_ws, data_null) = qaqc_functions.correction(station_name, log_file, data_ws, data_null, dt_array,
                                                             data_month, data_year, 3)
        # Correcting Precipitation
        elif user == 4:
            (data_precip, data_null) = qaqc_functions.correction(station_name, log_file, data_precip, data_null,
                                                                 dt_array, data_month, data_year, 4)
        # Correcting Solar radiation
        elif user == 5:
            (data_rs, data_null) = qaqc_functions.correction(station_name, log_file, data_rs, rso, dt_array,
                                                             data_month, data_year, 5)
        # Correcting Humidity Variable
        elif user == 6:
            # Variables passed depends on what variables were provided
            if column_df.ea != -1:
                # Vapor Pressure exists
                (data_ea, data_null) = qaqc_functions.correction(station_name, log_file, data_ea, data_null, dt_array,
                                                                 data_month, data_year, 7)

            elif column_df.ea == -1 and column_df.rhmax != -1 and column_df.rhmin != -1:
                # No vapor pressure but have rhmax and min
                (data_rhmax, data_rhmin) = qaqc_functions.correction(station_name, log_file, data_rhmax, data_rhmin,
                                                                     dt_array, data_month, data_year, 8)

            elif column_df.ea == -1 and column_df.rhmax == -1 and column_df.rhmin == -1 and column_df.rhavg != -1:
                # Only have RHavg
                (data_rhavg, data_null) = qaqc_functions.correction(station_name, log_file, data_rhavg, data_null,
                                                                    dt_array, data_month, data_year, 9)
            else:
                # If an unsupported combination of humidity variables is present, raise a value error.
                raise ValueError('Humidity correction section encountered an '
                                 'unexpected combination of humidity inputs.')
        else:
            # user quits, exit out of loop
            print('\nSystem: Now finishing up corrections.')
            break  # Break here because all recalculations were done at the end of the last loop iteration

        ##########
        # Now that a variable has been corrected, fill any variables and recalculate all relevant secondary variables
        if user == 1 or user == 2 or user == 5:

            if user == 1:  # User has corrected temperature, so fill all missing values with a normal distribution
                # Create mean monthly and standard deviation
                mm_tmax = np.zeros(12)
                mm_tmin = np.zeros(12)
                std_tmax = np.zeros(12)
                std_tmin = np.zeros(12)

                for k in range(12):
                    temp_indexes = np.where(data_month == k+1)[0]
                    temp_indexes = np.array(temp_indexes, dtype=int)
                    mm_tmax[k] = np.nanmean(data_tmax[temp_indexes])
                    std_tmax[k] = np.nanstd(data_tmax[temp_indexes])
                    mm_tmin[k] = np.nanmean(data_tmin[temp_indexes])
                    std_tmin[k] = np.nanstd(data_tmax[temp_indexes])


                # Fill missing observations with samples from a normal distribution with monthly mean and variance
                for i in range(data_length):
                    if np.isnan(data_tmax[i]):
                        data_tmax[i] = np.random.normal(mm_tmax[data_month[i] - 1], std_tmax[data_month[i] - 1], 1)
                        fill_tmax[i] = data_tmax[i]
                    else:
                        pass
                    if np.isnan(data_tmin[i]):
                        data_tmin[i] = np.random.normal(mm_tmin[data_month[i] - 1], std_tmin[data_month[i] - 1], 1)
                        fill_tmin[i] = data_tmin[i]
                    else:
                        pass
                    if (data_tmax[i] <= data_tmin[i]) or (data_tmax[i] - data_tmin[i] <= 3):
                        # This is not realistic, tmax needs to be warmer than tmin and daily temp isn't constant
                        # Fill this observation in with  mm observation with the difference of 1/2 of mm delta t
                        data_tmax[i] = mm_tmax[data_month[i] - 1] + (0.5 * mm_delta_t[data_month[i] - 1])
                        fill_tmax[i] = data_tmax[i]
                        data_tmin[i] = mm_tmin[data_month[i] - 1] - (0.5 * mm_delta_t[data_month[i] - 1])
                        fill_tmin[i] = data_tmin[i]
            else:
                pass
            # Figure out which humidity variables are provided and recalculate Ea and TDew if needed
            # This function is safe to use after correcting because it tracks what variable was provided by the data
            # and recalculates appropriately. It doesn't overwrite provided variables with calculated versions.
            # Ex. if only TDew is provided, it recalculates ea while returning original provided tdew
            (data_ea, data_tdew) = data_functions.calc_humidity_variables(data_tmax, data_tmin, data_tavg, data_ea,
                                                                          column_df.ea, data_tdew, column_df.tdew,
                                                                          data_rhmax, column_df.rhmax, data_rhmin,
                                                                          column_df.rhmin, data_rhavg, column_df.rhavg)

            # Recalculates secondary temperature values and mean monthly counterparts
            (delta_t, mm_delta_t, k_not, mm_k_not, mm_tmin, mm_tdew) = data_functions. \
                calc_temperature_variables(data_month, data_tmax, data_tmin, data_tdew)

            if user == 2 or user == 5:
                #####
                # Fill in any missing tdew data with tmin - k0 curve.
                # Once TDew is filled, if that filled index is also empty for ea, then we use filled tdew to calc ea
                # If ea is given and NOT empty at that index we do nothing to avoid overwriting actual data with filled
                # and the now filled TDew sections are used to calculate ea for those filled indices.
                # Nothing occurs if this fill code is run a second time because vars are already filled unless
                # correction methods throw out data.
                for i in range(data_length):
                    if np.isnan(data_tdew[i]):
                        data_tdew[i] = data_tmin[i] - mm_k_not[data_month[i] - 1]
                        fill_tdew[i] = data_tdew[i]

                        if column_df.ea == -1 or (column_df.ea != -1 and np.isnan(data_ea[i])):
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
        else:
            pass

        # Recalculates rso and grass/alfalfa reference evapotranspiration from refet package
        np.warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning for nans
        (rso, mm_rs, eto, etr, mm_eto, mm_etr) = data_functions. \
            calc_rso_and_refet(station_lat, station_elev, ws_anemometer_height, data_doy, data_month,
                               data_tmax, data_tmin, data_ea, data_ws, data_rs)
        np.warnings.resetwarnings()

    #########################
    # Final calculations
    # We calculate both original and optimized thornton running solar radiation, and then if we are correcting data
    # we fill in missing observations of solar radiation with optimized thornton running solar
    # then we fill in missing windspeed data with an exponential random distribution
    # finally recalculate reference evapotranspiration with the filled data_rs and data_ws
    (orig_rs_tr, mm_orig_rs_tr, opt_rs_tr, mm_opt_rs_tr) = data_functions. \
        calc_org_and_opt_rs_tr(mc_iterations, log_file, data_month, delta_t, mm_delta_t, data_rs, rso)

    if script_mode == 1:
        mm_ws = np.zeros(12)
        std_ws = np.zeros(12)
        for k in range(12):
            temp_indexes = np.where(data_month == k + 1)[0]
            temp_indexes = np.array(temp_indexes, dtype=int)
            mm_ws[k] = np.nanmean(data_ws[temp_indexes])
            std_ws[k] = np.nanmean(data_ws[temp_indexes])

        for i in range(data_length):
            # loop to fill data_rs with rs_tr and data_ws with an exponential function centered on mm_ws for that month
            if np.isnan(data_rs[i]):
                data_rs[i] = opt_rs_tr[i]
                fill_rs[i] = opt_rs_tr[i]
            else:
                # If rs isn't empty then nothing is required to be done.
                pass
            if np.isnan(data_ws[i]):
                data_ws[i] = np.random.normal(mm_ws[data_month[i] - 1], std_ws[data_month[i] - 1], 1)

                if data_ws[i] < 0.2:  # check to see if filled windspeed is lower than reasonable
                    data_ws[i] = 0.2
                else:
                    pass
                fill_ws[i] = data_ws[i]
            else:
                # If ws isn't empty then nothing is required to be done.
                pass

        # Recalculate eto and etr one final time
        (rso, mm_rs, eto, etr, mm_eto, mm_etr) = data_functions. \
            calc_rso_and_refet(station_lat, station_elev, ws_anemometer_height, data_doy,
                               data_month, data_tmax, data_tmin, data_ea, data_ws, data_rs)
    else:
        pass

    #########################
    # Generate bokeh composite plot
    # Creates one large plot featuring all variables as subplots, used to get a concise overview of the full dataset
    # If user opts to not correct data (sets script_mode = 0), then this plots data before correction
    # If user does correct data, then this plots data after correction
    print("\nSystem: Now creating composite bokeh graph.")
    if generate_bokeh:  # Flag to create graphs or not
        plot_list = []
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
        plot_tmax_tmin = plotting_functions.line_plot(x_size, y_size, dt_array, data_tmax, data_tmin, 1, '')
        plot_list.append(plot_tmax_tmin)
        # Temperature Minimum and Dewpoint Plot
        plot_tmin_tdew = plotting_functions.line_plot(x_size, y_size, dt_array, data_tmin, data_tdew, 2, '',
                                                      plot_tmax_tmin)
        plot_list.append(plot_tmin_tdew)

        # Subplot 3 changes based on what variables are provided
        if column_df.ea != -1:  # Vapor pressure was provided
            plot_humid = plotting_functions.line_plot(x_size, y_size, dt_array, data_ea, data_null, 7, 'Provided ',
                                                      plot_tmax_tmin)
        elif column_df.ea == -1 and column_df.tdew != -1:  # Tdew was provided, show calculated vapor pressure
            plot_humid = plotting_functions.line_plot(x_size, y_size, dt_array, data_ea, data_null, 7, 'Calculated ',
                                                      plot_tmax_tmin)
        elif column_df.ea == -1 and column_df.tdew == -1 and column_df.rhmax != -1 and column_df.rhmin != -1:  # RH max
            plot_humid = plotting_functions.line_plot(x_size, y_size, dt_array, data_rhmax, data_rhmin, 8, '',
                                                      plot_tmax_tmin)
        elif column_df.ea == -1 and column_df.tdew == -1 and column_df.rhmax == -1 and column_df.rhavg != -1:  # RHavg
            plot_humid = plotting_functions.line_plot(x_size, y_size, dt_array, data_rhavg, data_null, 9, '',
                                                      plot_tmax_tmin)
        else:
            # If an unsupported combination of humidity variables is present, raise a value error.
            raise ValueError('Bokeh figure generation encountered an unexpected combination of humidity inputs.')

        plot_list.append(plot_humid)

        # If both ea and rhmax/rhmin are provided, generate a supplementary rhmax/min graph
        if column_df.rhmax != -1 and column_df.rhmin != -1 and column_df.ea != -1:
            plot_supplemental_rh = plotting_functions.line_plot(x_size, y_size, dt_array, data_rhmax, data_rhmin, 8, '',
                                                            plot_tmax_tmin)
            plot_list.append(plot_supplemental_rh)

        # Mean Monthly Temperature Minimum and Dewpoint
        plot_mm_tmin_tdew = plotting_functions.line_plot(x_size, y_size, mm_dt_array, mm_tmin, mm_tdew, 2, 'MM ')
        plot_list.append(plot_mm_tmin_tdew)

        # Mean Monthly k0 curve (Tmin-Tdew)
        plot_mm_k_not = plotting_functions.line_plot(x_size, y_size, mm_dt_array, mm_k_not, data_null, 10, '',
                                                     plot_mm_tmin_tdew)
        plot_list.append(plot_mm_k_not)

        # Solar radiation and clear sky solar radiation
        plot_rs_rso = plotting_functions.line_plot(x_size, y_size, dt_array, data_rs, rso, 5, '', plot_tmax_tmin)
        plot_list.append(plot_rs_rso)

        # Windspeed
        plot_ws = plotting_functions.line_plot(x_size, y_size, dt_array, data_ws, data_null, 3, '', plot_tmax_tmin)
        plot_list.append(plot_ws)

        # Precipitation
        plot_precip = plotting_functions.line_plot(x_size, y_size, dt_array, data_precip, data_null, 4,
                                                   '', plot_tmax_tmin)
        plot_list.append(plot_precip)

        # Optimized mean monthly Thornton-Running solar radiation and Mean Monthly solar radiation
        plot_mm_opt_rs_tr = plotting_functions.line_plot(x_size, y_size, mm_dt_array, mm_rs, mm_opt_rs_tr, 6,
                                                         'MM Optimized ', plot_mm_tmin_tdew)
        plot_list.append(plot_mm_opt_rs_tr)

        # Optimized mean monthly Thornton-Running solar radiation and Mean Monthly solar radiation
        plot_mm_orig_rs_tr = plotting_functions.line_plot(x_size, y_size, mm_dt_array, mm_rs, mm_orig_rs_tr, 6,
                                                          'MM Original ', plot_mm_tmin_tdew)
        plot_list.append(plot_mm_orig_rs_tr)


        # Now construct grid plot out of all of the subplots
        number_of_plots = len(plot_list)
        number_of_rows = ceil(number_of_plots / gridplot_columns)
        # TODO: why does replacing below 1 with gridplot_columns cause an error?
        grid_of_plots = [([None] * 1) for i in range(number_of_rows)]

        for i in range(number_of_rows):
            for j in range(gridplot_columns):

                if len(plot_list) > 0:
                    grid_of_plots[i][j] = plot_list.pop(0)
                else:
                    pass

        fig = gridplot(grid_of_plots, toolbar_location='left')
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
                              'TAvg (C)': data_tavg, 'TMax (C)': data_tmax, 'TMin (C)': data_tmin,
                              'TDew (C)': data_tdew, 'Vapor Pres (kPa)': data_ea, 'RHAvg (%)': data_rhavg,
                              'RHMax (%)': data_rhmax, 'RHMin (%)': data_rhmin, 'Rs (w/m2)': data_rs,
                              'Opt_Rs_TR (w/m2)': opt_rs_tr, 'Rso (w/m2)': rso, 'Windspeed (m/s)': data_ws,
                              'Precip (mm)': data_precip, 'ETr (mm)': etr, 'ETo (mm)': eto, 'ws_2m (m/s)': ws_2m},
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
                            'TMax (C)': fill_tmax, 'TMin (C)': fill_tmin, 'TDew (C)': fill_tdew,
                            'Vapor Pres (kPa)': fill_ea, 'Rs (w/m2)': fill_rs}, index=datetime_df)

    # Open up pandas excel writer
    output_writer = pd.ExcelWriter(station_name + "_output" + ".xlsx", engine='xlsxwriter')
    # Convert data frames to xlsxwriter excel objects
    output_df.to_excel(output_writer, sheet_name='Corrected Data', na_rep=missing_fill_value)
    delta_df.to_excel(output_writer, sheet_name='Delta (Corr - Orig)', na_rep=missing_fill_value)
    fill_df.to_excel(output_writer, sheet_name='Filled Data', na_rep=missing_fill_value)
    # Save output file
    output_writer.save()

    logger = open(log_file, 'a')
    if script_mode == 1:
        if np.isnan(eto).any() or np.isnan(etr).any():
            print("\nSystem: After finishing corrections and filling data, ETr and ETo still had missing observations.")
            logger.write('After finishing corrections and filling data, ETr and ETo still had missing observations. \n')
        else:
            logger.write('The output file for this station has a complete record of ETo and ETr observations. \n')
    else:
        pass
    logger.write('\nThe file has been successfully processed and output files saved at %s.' %
                 dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.close()



# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")

