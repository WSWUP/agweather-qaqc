import bokeh.plotting
from bokeh.layouts import gridplot
from bokeh.plotting import output_file, reset_output, save
import datetime as dt
from math import ceil
import numpy as np
import os
import pandas as pd
from qaqc_modules import data_functions, input_functions, plotting_functions, qaqc_functions
from refet.calcs import _wind_height_adjust


class WeatherQAQC:

    def __init__(self, config_file_path='config.ini', metadata_file_path=None, gridplot_columns=1):
        self.config_path = config_file_path
        self.metadata_path = metadata_file_path
        self.gridplot_columns = gridplot_columns

    def _obtain_data(self):
        """
            Obtain initial data and put it into a dataframe
        """
        (self.data_df, self.column_df, self.metadata_df, self.metadata_series, self.config_dict) = \
            input_functions.obtain_data(self.config_path, self.metadata_path)

        # todo this individual assignment section is only temporary as the config_dict of input functions will be
        #    referenced though this script eventually
        self.station_name = self.config_dict['station_name']
        self.log_file = self.config_dict['log_file_path']
        self.station_lat = self.config_dict['station_latitude']
        self.station_lon = self.config_dict['station_longitude']
        self.station_elev = self.config_dict['station_elevation']
        self.ws_anemometer_height = self.config_dict['anemometer_height']
        self.missing_fill_value = self.config_dict['missing_fill_value']
        self.folder_path = self.config_dict['folder_path']

        self.script_mode = self.config_dict['corr_flag']
        self.auto_mode = self.config_dict['auto_flag']
        self.fill_mode = self.config_dict['fill_flag']
        self.generate_bokeh = self.config_dict['plot_flag']

        if self.script_mode == 1:  # correcting data
            self.mc_iterations = 1000  # Number of iters for MC simulation of thornton running solar radiation gen
        else:
            self.mc_iterations = 50  # if we're not correcting data then only do a few iterations to save time

        print("\nSystem: Raw data successfully extracted from station file.")

        # Extract individual variables from data frame back into to numpy arrays.
        self.data_year = np.array(self.data_df.year)
        self.data_month = np.array(self.data_df.month)
        self.data_day = np.array(self.data_df.day)
        self.data_tavg = np.array(self.data_df.tavg)
        self.data_tmax = np.array(self.data_df.tmax)
        self.data_tmin = np.array(self.data_df.tmin)
        self.data_tdew = np.array(self.data_df.tdew)
        self.data_ea = np.array(self.data_df.ea)
        self.data_rhavg = np.array(self.data_df.rhavg)
        self.data_rhmax = np.array(self.data_df.rhmax)
        self.data_rhmin = np.array(self.data_df.rhmin)
        self.data_rs = np.array(self.data_df.rs)
        self.data_ws = np.array(self.data_df.ws)
        self.data_precip = np.array(self.data_df.precip)

        self.output_file_path = self.folder_path + "/correction_files/" + self.station_name + "_output" + ".xlsx"

    def _calculate_secondary_vars(self):
        """
            Calculate secondary variables from initial ones
        """
        print("\nSystem: Now calculating secondary variables based on data provided.")
        self.data_length = self.data_year.shape[0]
        self.station_pressure = 101.3 * (((293 - (0.0065 * self.station_elev)) / 293) ** 5.26)  # units kPa, EQ 3 ASCE

        # Calculate DOY from Y/M/D values
        self.data_doy = []
        for i in range(self.data_length):
            # Create list of string DOY values
            self.data_doy.append(dt.date(self.data_year[i], self.data_month[i], self.data_day[i]).strftime("%j"))

        self.data_doy = np.array(list(map(int, self.data_doy)))  # Converts list of string values into ints

        # Calculate tavg if it is not provided by dataset
        if self.column_df.tavg == -1:
            # Tavg not provided
            self.data_tavg = np.array((self.data_tmax + self.data_tmin) / 2.0)
        else:
            # Tavg is provided, no action needs to be taken
            pass

        # Figure out which humidity variables are provided and calculate Ea and TDew if needed
        (self.data_ea, self.data_tdew) = data_functions.\
            calc_humidity_variables(self.data_tmax, self.data_tmin, self.data_tavg, self.data_ea, self.column_df.ea,
                                    self.data_tdew, self.column_df.tdew, self.data_rhmax, self.column_df.rhmax,
                                    self.data_rhmin, self.column_df.rhmin, self.data_rhavg, self.column_df.rhavg)

        # Calculates secondary temperature values and mean monthly counterparts
        (self.delta_t, self.mm_delta_t, self.k_not, self.mm_k_not, self.mm_tmin, self.mm_tdew) = data_functions. \
            calc_temperature_variables(self.data_month, self.data_tmax, self.data_tmin, self.data_tdew)

        '''
            Tdew_ko will have all missing values of tdew filled in with tmin - Ko curve method, but will keep missing
            values if the underlying tmin is also missing. Currently it is just a copy of TDew, but filling will occur
            after temp/humidity has been corrected. If the user does not correct data then this will stay unfilled, but
            that is an edge case and not the intent of this code
            
            Tdew_ko is distinct from complete_tdew in that it only fills in an day's observation if there is a 
            tmin observation presentfor that day. Complete_tdew has a filled in observation for every day because it is
            based on a tmin that has been filled with random samples from a normal distribution. Unless the user 
            specifically asks for this simulated data to be saved then it is only used to create a complete record of 
            Rso for Rs correction and then is discarded.
        '''
        self.data_tdew_ko = np.array(self.data_tdew)

        '''
            This script uses multiple vapor pressure (ea) variables. As a reference for readability:
    
            data_ea = either ea data provided by the station or ea that has been calculated by whatever the 'best'
                      humidity variable was in the input file. If it is the latter, this ea will have all the gaps and
                      issues (like drift) that the underlying variable had.
    
            compiled_ea = the script creates as complete a record as possible of ea values by calculating ea from 
                       'worse' variables should there be gaps in the more preferred ones. It only samples from data 
                       that has been provided by the dataset. By the end of this process, the only gaps that will exist 
                       will match the gaps that exist within Tmin. The preference is as follows:
    
                       (provided) Ea > (provided) TDew > RH Max and Min > RH Avg > TDew generated from TMin - Ko curve
    
            complete_ea = this is compiled ea but with all of the gaps filled in with TDew generated from 
                       TMin - Ko Curve, and all gaps in TMin filled in by sampling from a monthly normal distribution
                       of values. Unless the user specifically wants to export this day (option is in config file)
                       then this data is only used to create a complete record of Rso values for Rs correction,
                       and then is discarded at the end.
        '''
        self.compiled_ea = data_functions.compile_ea(self.data_tmax, self.data_tmin, self.data_tavg,
                                                     self.data_ea, self.data_tdew, self.column_df.tdew,
                                                     self.data_rhmax, self.column_df.rhmax, self.data_rhmin,
                                                     self.column_df.rhmin, self.data_rhavg,
                                                     self.column_df.rhavg, self.data_tdew_ko)

        # Calculates rso and grass/alfalfa reference evapotranspiration from refet package
        np.warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning for nans
        (self.rso, self.mm_rs, self.eto, self.etr, self.mm_eto, self.mm_etr) = data_functions.\
            calc_rso_and_refet(self.station_lat, self.station_elev, self.ws_anemometer_height, self.data_doy,
                               self.data_month, self.data_tmax, self.data_tmin, self.compiled_ea, self.data_ws,
                               self.data_rs)
        np.warnings.resetwarnings()  # reset warning filter to default

        #########################
        # Back up original data
        # Original data will be saved to output file
        # Values are also used to generate delta values of corrected data - original data
        self.original_df = self.data_df.copy(deep=True)  # Create an unlinked copy of read-in values dataframe
        self.original_df['rso'] = self.rso
        self.original_df['etr'] = self.etr
        self.original_df['eto'] = self.eto
        self.original_df['compiled_ea'] = self.compiled_ea

        # Create datetime variables that will be used by bokeh plot and correction functions
        self.dt_array = []
        for i in range(self.data_length):
            self.dt_array.append(dt.datetime(self.data_year[i], self.data_month[i], self.data_day[i]))
        self.dt_array = np.array(self.dt_array, dtype=np.datetime64)
        self.mm_dt_array = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        self.data_null = np.empty(self.data_length) * np.nan

    def _correct_data(self):
        """
            Correct data
        """
        #########################
        # Correcting Data
        # Loop where user selects an option, corrects it, script recalculates, and then loops.
        # If user opts to not correct data (sets script_mode = 0),
        # then skips this section and just generates composite plot
        if self.script_mode == 1:
            print("\nSystem: Now beginning correction on data.")
        else:
            print("\nSystem: Skipping data correction and plotting raw data.")

        # create a flag to check if composite ea has been adjusted or not before correcting solar radiation
        self.humidity_adjusted = False

        # Complete_vars are going to be filled for the whole record, which may be put into output file if user requests
        self.complete_tmax = np.array(self.data_tmax)
        self.complete_tmin = np.array(self.data_tmin)
        self.complete_ea = np.array(self.compiled_ea)
        self.complete_tdew = np.array(self.data_tdew)

        # Create arrays that will track which values have been filled (replace missing data) by the script
        self.fill_tmax = np.zeros(self.data_length)
        self.fill_tmin = np.zeros(self.data_length)
        self.fill_ea = np.zeros(self.data_length)
        self.fill_tdew = np.zeros(self.data_length)
        self.fill_rs = np.zeros(self.data_length)
        self.fill_ws = np.zeros(self.data_length)
        self.fill_rso = np.zeros(self.data_length)

        # Begin loop for correcting variables
        while self.script_mode == 1:
            reset_output()  # clears bokeh output, prevents ballooning file sizes
            print('\nPlease select which of the following variables you want to correct'
                  '\n   Enter 1 for TMax and TMin.'
                  '\n   Enter 2 for TMin and TDew, if TDew was provided.'
                  '\n   Enter 3 for Windspeed.'
                  '\n   Enter 4 for Precipitation.'
                  '\n   Enter 5 for Solar Radiation (Rs).'
                  '\n   Enter 6 for Vapor Pressure (Ea), if it was provided.'
                  '\n   Enter 7 for RH Maximum and Minimum, if they were provided.'
                  '\n   Enter 8 for RH Average, if it was provided.'
                  '\n   Enter 9 to adjust how compiled humidity is sourced.'
                  '\n   Enter 0 to stop applying corrections.'
                  )

            user = int(input("\nEnter your selection: "))
            choice_loop = 1
            while choice_loop:
                if 0 <= user <= 9:
                    # The following if statements check if user tries to correct a variable that was not provided
                    # or make sure correction is being done in the right manner
                    if user == 2 and self.column_df.tdew == -1:
                        print('\nDewpoint temperature was not provided by the file, please choose a different option.')
                        user = int(input('Specify which variable you would like to correct: '))

                    elif user == 5 and not self.humidity_adjusted:
                        print('\n\nBefore correcting solar radiation, did you want to adjust compiled humidity?.')
                        print('Doing so may allow you to get the best possible humidity record for Rs correction.')
                        print('\nEnter 1 to adjust compiled humidity or 0 to skip.')

                        humid_loop = 1
                        while humid_loop:
                            humid_choice = int(input('Enter your selection: '))
                            if humid_choice == 0:
                                # user is choosing to skip humidity adjustment so nothing needs to be done.
                                humid_loop = 0
                            elif humid_choice == 1:
                                # change original choice to the adjust humidity option
                                user = 9
                                humid_loop = 0
                            else:
                                # non valid choice entered
                                print('\nPlease enter a valid option.')

                        choice_loop = 0

                    elif user == 6 and self.column_df.ea == -1:
                        print('\nVapor Pressure was not provided by the file, please choose a different option.')
                        user = int(input('Specify which variable you would like to correct: '))

                    elif user == 7 and (self.column_df.rhmax == -1 or self.column_df.rhmin == -1):
                        print('\nRHMax and RHMin were not provided by the file, please choose a different option.')
                        user = int(input('Specify which variable you would like to correct: '))

                    elif user == 8 and self.column_df.rhavg == -1:
                        print('\nRHAvg was not provided by the file, please choose a different option.')
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
                (self.data_tmax, self.data_tmin) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_tmax, self.data_tmin, self.dt_array,
                               self.data_month, self.data_year, 1, self.auto_mode)
            # Correcting Min/Dew Temperature data
            elif user == 2:
                (self.data_tmin, self.data_tdew) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_tmin, self.data_tdew, self.dt_array,
                               self.data_month, self.data_year, 2, self.auto_mode)
            # Correcting Windspeed
            elif user == 3:
                (self.data_ws, self.data_null) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_ws, self.data_null, self.dt_array,
                               self.data_month, self.data_year, 3, self.auto_mode)
            # Correcting Precipitation
            elif user == 4:
                (self.data_precip, self.data_null) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_precip, self.data_null, self.dt_array,
                               self.data_month, self.data_year, 4, self.auto_mode)
            # Correcting Solar radiation
            elif user == 5:
                (self.data_rs, self.data_null) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_rs, self.rso, self.dt_array,
                               self.data_month, self.data_year, 5, self.auto_mode)
            # Correcting Vapor Pressure
            elif user == 6:
                (self.data_ea, self.data_null) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_ea, self.data_null, self.dt_array,
                               self.data_month, self.data_year, 7, self.auto_mode)
            # Correcting Relative Humidity Max and Min
            elif user == 7:
                (self.data_rhmax, self.data_rhmin) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_rhmax, self.data_rhmin, self.dt_array,
                               self.data_month, self.data_year, 8, self.auto_mode)
            # Correcting Relative Humidity Average
            elif user == 8:
                (self.data_rhavg, self.data_null) = qaqc_functions.\
                    correction(self.station_name, self.log_file, self.folder_path,
                               self.data_rhavg, self.data_null, self.dt_array,
                               self.data_month, self.data_year, 9, self.auto_mode)
            # Adjusting compiled_ea
            elif user == 9:
                self.compiled_ea = qaqc_functions.\
                    compiled_humidity_adjustment(self.station_name, self.log_file, self.folder_path, self.dt_array,
                                                 self.data_tmax, self.data_tmin, self.data_tavg, self.compiled_ea,
                                                 self.data_ea, self.column_df.ea, self.data_tdew, self.column_df.tdew,
                                                 self.data_tdew_ko, self.data_rhmax, self.column_df.rhmax,
                                                 self.data_rhmin, self.column_df.rhmin,
                                                 self.data_rhavg, self.column_df.rhavg)

                self.humidity_adjusted = True
            else:
                # todo make this more explicit and handle user input that isnt strictly int without breaking
                # user quits, exit out of loop
                print('\nSystem: Now finishing up corrections.')
                # Break here because all recalculations were done at the end of the last loop iteration
                # also we break as opposed to setting script_mode to 0 because it is used later in the program
                break

            if 1 <= user <= 2 or 6 <= user <= 8:
                if user == 1:  # User has corrected temperature, so fill all missing values with a normal distribution

                    # Reset 'complete' vars as the underlying var has been changed.
                    self.complete_tmax = np.array(self.data_tmax)
                    self.complete_tmin = np.array(self.data_tmin)

                    # Remove corresponding TAvg observations after outliers have been removed from TMax and TMin
                    tmax_removed_indices = np.array(np.where(np.isnan(self.data_tmax)))  # array of indices of nans
                    tmin_removed_indices = np.array(np.where(np.isnan(self.data_tmin)))  # array of indices of nans
                    self.data_tavg[tmax_removed_indices] = np.nan
                    self.data_tavg[tmin_removed_indices] = np.nan

                    # Create mean monthly and standard deviation
                    self.mm_tmax = np.zeros(12)
                    self.mm_tmin = np.zeros(12)
                    self.std_tmax = np.zeros(12)
                    self.std_tmin = np.zeros(12)

                    for k in range(12):
                        temp_indexes = np.where(self.data_month == k+1)[0]
                        temp_indexes = np.array(temp_indexes, dtype=int)
                        self.mm_tmax[k] = np.nanmean(self.data_tmax[temp_indexes])
                        self.std_tmax[k] = np.nanstd(self.data_tmax[temp_indexes])
                        self.mm_tmin[k] = np.nanmean(self.data_tmin[temp_indexes])
                        self.std_tmin[k] = np.nanstd(self.data_tmin[temp_indexes])

                    # Fill missing observations with samples from a normal distribution with monthly mean and variance
                    for i in range(self.data_length):
                        if np.isnan(self.data_tmax[i]):
                            self.complete_tmax[i] = np.random.normal(self.mm_tmax[self.data_month[i] - 1],
                                                                     self.std_tmax[self.data_month[i] - 1], 1)
                            self.fill_tmax[i] = self.complete_tmax[i]
                        else:
                            pass

                        if np.isnan(self.data_tmin[i]):
                            self.complete_tmin[i] = np.random.normal(self.mm_tmin[self.data_month[i] - 1],
                                                                     self.std_tmin[self.data_month[i] - 1], 1)
                            self.fill_tmin[i] = self.complete_tmin[i]
                        else:
                            pass

                        if (self.complete_tmax[i] <= self.complete_tmin[i]) or \
                                (self.complete_tmax[i] - self.complete_tmin[i] <= 3):
                            # This is a logical check to make sure that tmax is sufficiently distant from tmin once
                            # they have been filled in, tmax needs to be warmer than tmin and daily temp isn't constant
                            # so there should be at least a small difference in tmax-tmin

                            # todo the below lines always provide a higher than average tmax
                            #   and a lower than average tmin, this can be improved
                            # Fill this observation in with  mm observation with the difference of 1/2 of mm delta t
                            self.complete_tmax[i] = self.mm_tmax[self.data_month[i] - 1] + \
                                                    (0.5 * self.mm_delta_t[self.data_month[i] - 1])
                            self.fill_tmax[i] = self.complete_tmax[i]

                            self.complete_tmin[i] = self.mm_tmin[self.data_month[i] - 1] - \
                                (0.5 * self.mm_delta_t[self.data_month[i] - 1])
                            self.fill_tmin[i] = self.complete_tmin[i]
                        else:
                            # data is different enough to appear valid
                            pass

                    if self.fill_mode:
                        # we are filling in data, so copy all of the filled versions onto the original temperature
                        self.data_tmax = np.array(self.complete_tmax)
                        self.data_tmin = np.array(self.complete_tmin)
                    else:
                        # if we are not filling, we will hold the copies to later fill in rso, but will reset fill
                        # tracking variables
                        self.fill_tmax = np.zeros(self.data_length)
                        self.fill_tmin = np.zeros(self.data_length)
                else:
                    # user did not correct option 1
                    pass

                # Figure out which humidity variables are provided and recalculate Ea and TDew if needed
                # This function is safe to use after correcting because it tracks what variable was provided by the data
                # and recalculates appropriately. It doesn't overwrite provided variables with calculated versions.
                # Ex. if only TDew is provided, it recalculates ea while returning original provided tdew
                (self.data_ea, self.data_tdew) = data_functions.\
                    calc_humidity_variables(self.data_tmax, self.data_tmin, self.data_tavg, self.data_ea,
                                            self.column_df.ea, self.data_tdew, self.column_df.tdew,
                                            self.data_rhmax, self.column_df.rhmax, self.data_rhmin,
                                            self.column_df.rhmin, self.data_rhavg, self.column_df.rhavg)

                # Recalculates secondary temperature values and mean monthly counterparts
                (self.delta_t, self.mm_delta_t, self.k_not, self.mm_k_not, self.mm_tmin, self.mm_tdew) = \
                    data_functions.calc_temperature_variables(self.data_month, self.data_tmax,
                                                              self.data_tmin, self.data_tdew)

                # Since we are recalculating humidity variables, we also need to reset tdew_ko to ensure it matches the
                # underlying unfilled tdew. It is filled later after this once the user corrects a humidity var
                # so this reset is acceptable
                self.data_tdew_ko = np.array(self.data_tdew)

                if user == 2 or 6 <= user <= 8:

                    # Reset 'complete' version as underlying variable may have changed
                    self.complete_tdew = np.array(self.data_tdew)
                    '''
                        Fill in any missing tdew data with tmin - k0 curve.
                        
                        As detailed above, data_tdew_ko only fills in missing tdew observations with real tmin obs,
                        while complete_tdew is a full record filled in using a filled in tmin.
                        
                        Nothing occurs if this fill code is run a second time because vars are already filled unless
                        correction methods throw out data, in which case we need to refill for the complete record
                        that Rs correction requires.
                    '''
                    for i in range(self.data_length):
                        if np.isnan(self.data_tdew[i]):

                            # Tdew_ko will have gaps that match gaps in Tmin
                            # Complete_tdew will match complete_tmin in having no gaps
                            self.data_tdew_ko[i] = self.data_tmin[i] - self.mm_k_not[self.data_month[i] - 1]
                            self.complete_tdew[i] = self.complete_tmin[i] - self.mm_k_not[self.data_month[i] - 1]
                            self.fill_tdew[i] = self.complete_tdew[i]
                        else:
                            # If TDew isn't empty then nothing is required to be done.
                            pass

                    if self.fill_mode:
                        # we are filling in data, so copy all of the filled versions onto the original arrays
                        self.data_tdew = np.array(self.complete_tdew)
                    else:
                        # if we are not filling, we will hold the copies to later fill in rso, but will reset fill
                        # tracking variables
                        self.fill_tdew = np.zeros(self.data_length)
                else:
                    # user did not select option 2 or 6-8
                    pass

                '''
                    Recreate the 'compiled' ea as temperature or humidity vars were corrected and may have changed the
                    data underlying the compiled ea. Once that is done we will fill in all the gaps with the 
                    variable 'complete_tdew' so that a complete record of ea exists for rs correction
                    
                    The gaps in compiled_ea are reset every time temperature or humidity is corrected so this code is 
                    okay to run multiple times
                '''
                self.compiled_ea = data_functions.compile_ea(self.data_tmax, self.data_tmin, self.data_tavg,
                                                             self.data_ea, self.data_tdew, self.column_df.tdew,
                                                             self.data_rhmax, self.column_df.rhmax, self.data_rhmin,
                                                             self.column_df.rhmin, self.data_rhavg,
                                                             self.column_df.rhavg, self.data_tdew_ko)

                # Reset 'complete' version as underlying variable may have changed.
                self.complete_ea = np.array(self.compiled_ea)

                for i in range(self.data_length):
                    if np.isnan(self.compiled_ea[i]):
                        self.complete_ea[i] = (0.6108 * np.exp((17.27 * self.complete_tdew[i]) / (self.complete_tdew[i]
                                                                                                  + 237.3)))
                        self.fill_ea[i] = self.complete_ea[i]
                else:
                    # Ea is provided and the index is not empty, do nothing to avoid overwriting actual data
                    pass

                if self.fill_mode:
                    # we are filling in data, so copy all of the filled versions onto the original arrays
                    self.data_ea = np.array(self.complete_ea)
                    self.compiled_ea = np.array(self.complete_ea)
                else:
                    # if we are not filling, we will hold the copies to later fill in rso, but will reset fill
                    # tracking variables
                    self.fill_ea = np.zeros(self.data_length)

            elif user == 9:  # User has adjusted how the compiled humidity is sourced, recreate complete_ea
                self.complete_ea = np.array(self.compiled_ea)

                for i in range(self.data_length):
                    if np.isnan(self.compiled_ea[i]):
                        self.complete_ea[i] = (0.6108 * np.exp((17.27 * self.complete_tdew[i]) /
                                                               (self.complete_tdew[i] + 237.3)))
                        self.fill_ea[i] = self.complete_ea[i]
                else:
                    # the index is not empty, do nothing to avoid overwriting actual data
                    pass

                if self.fill_mode:
                    # we are filling in data, so copy all of the filled versions onto the original arrays
                    self.data_ea = np.array(self.complete_ea)
                    self.compiled_ea = np.array(self.complete_ea)
                else:
                    # if we are not filling, we will hold the copies to later fill in rso, but will reset fill
                    # tracking variables
                    self.fill_ea = np.zeros(self.data_length)
            else:
                # user did not select options 1,2, 6, 7, 8, or 9.
                pass

            '''
                Even if the user doesn't want to put filled data into their output file, we still need to use complete
                records to get a complete record of Rso for use in Rs correction. This completed rso is only used for 
                this step and is not written as data to the output file
            '''
            if self.fill_mode:
                '''                  
                    This recalculates Rso and ETr values using the filled 'completed_' versions to provide a complete
                    record of ETr values.
                    
                    If this code is executing then 'data_' vars have already been replaced by their 'completed_' 
                    versions so the code is accurate in calling them 'data_'
                '''
                np.warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning, nans
                (self.rso, self.mm_rs, self.eto, self.etr, self.mm_eto, self.mm_etr) = data_functions. \
                    calc_rso_and_refet(self.station_lat, self.station_elev, self.ws_anemometer_height, self.data_doy,
                                       self.data_month, self.data_tmax, self.data_tmin, self.data_ea, self.data_ws,
                                       self.data_rs)
                np.warnings.resetwarnings()
            else:
                '''
                    User doesn't want to keep filled in data, so use complete versions to create a filled version of
                    rso while saving the other outputs of calc_rso_and_refet as temporary names which are unused to 
                    prevent them from impacting later calculations
                '''
                np.warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning, nans
                (self.rso, self._mm_rs, self._eto, self._etr, self._mm_eto, self._mm_etr) = \
                    data_functions.calc_rso_and_refet(self.station_lat, self.station_elev, self.ws_anemometer_height,
                                                      self.data_doy, self.data_month, self.complete_tmax,
                                                      self.complete_tmin, self.complete_ea, self.data_ws, self.data_rs)
                np.warnings.resetwarnings()

        '''
            At this point the user has finished correcting all variables they want to.
            
            We calculate both original and optimized thornton running solar radiation using a monte carlo approach
            The number of MC iterations is defined by script_mode. Additionally, if the user is electing to fill data 
            then we fill in all gaps of data_rs with the optimized thornton running solar radiation.
            
            Also, only if the user wants, we fill in all gaps of wind data using samples from a normal distribution.
            
            Finally, we do one final calculation of Rso/ETr with all the final versions of variables. If the user does
            NOT want to fill in data, this final calculation of Rso will replace the filled one used for Solar
            Radiation correction with one using only real data.
        '''

        (self.orig_rs_tr, self.mm_orig_rs_tr, self.opt_rs_tr, self.mm_opt_rs_tr) = data_functions. \
            calc_org_and_opt_rs_tr(self.mc_iterations, self.log_file, self.data_month, self.delta_t, self.mm_delta_t,
                                   self.data_rs, self.rso)

        # todo this section of code is out of place, currently we are not filling data but it could be situated better
        if self.script_mode == 1:
            self.mm_ws = np.zeros(12)
            self.std_ws = np.zeros(12)
            for k in range(12):
                temp_indexes = np.where(self.data_month == k + 1)[0]
                temp_indexes = np.array(temp_indexes, dtype=int)
                self.mm_ws[k] = np.nanmean(self.data_ws[temp_indexes])
                self.std_ws[k] = np.nanmean(self.data_ws[temp_indexes])

            if self.fill_mode:
                for i in range(self.data_length):
                    # fill data_rs with rs_tr and data_ws with an exponential function centered on mm_ws for that month
                    if np.isnan(self.data_rs[i]):
                        self.data_rs[i] = self.opt_rs_tr[i]
                        self.fill_rs[i] = self.opt_rs_tr[i]
                    else:
                        # If rs isn't empty then nothing is required to be done.
                        pass
                    if np.isnan(self.data_ws[i]):
                        self.data_ws[i] = np.random.normal(self.mm_ws[self.data_month[i] - 1],
                                                           self.std_ws[self.data_month[i] - 1], 1)

                        if self.data_ws[i] < 0.2:  # check to see if filled windspeed is lower than reasonable
                            self.data_ws[i] = 0.2
                        else:
                            pass

                        self.fill_ws[i] = self.data_ws[i]
                    else:
                        # If ws isn't empty then nothing is required to be done.
                        pass
            else:
                pass

            # Recalculate eto and etr one final time
            # This also overwrites the filled Rso, so we will create a copy for posterity
            self.fill_rso = np.array(self.rso)

            (self.rso, self.mm_rs, self.eto, self.etr, self.mm_eto, self.mm_etr) = data_functions. \
                calc_rso_and_refet(self.station_lat, self.station_elev, self.ws_anemometer_height, self.data_doy,
                                   self.data_month, self.data_tmax, self.data_tmin, self.compiled_ea,
                                   self.data_ws, self.data_rs)
        else:
            # script_mode == 0 so we are not correcting data and we do not generate filled versions or need to recalc
            # secondary vars
            pass

    def _create_plots(self):
        """
            Makes and saves histogram and composite plots.
        """
        #########################
        # Histograms of original data
        # Generates composite plot of specific variables before correction
        # We fill these variables by sampling a normal distribution, so we use this plot mainly as evidence for that.
        if self.generate_bokeh and self.script_mode == 0:
            ws_hist = plotting_functions.histogram_plot(self.data_ws[~np.isnan(self.data_ws)],
                                                        'Windspeed', 'black', 'm/s')
            tmax_hist = plotting_functions.histogram_plot(self.data_tmax[~np.isnan(self.data_tmax)],
                                                          'TMax', 'red', 'degrees C')
            tmin_hist = plotting_functions.histogram_plot(self.data_tmin[~np.isnan(self.data_tmin)],
                                                          'TMin', 'blue', 'degrees C')
            tavg_hist = plotting_functions.histogram_plot(self.data_tmin[~np.isnan(self.data_tmin)],
                                                          'TAvg', 'black', 'degrees C')
            tdew_hist = plotting_functions.histogram_plot(self.data_tdew[~np.isnan(self.data_tdew)],
                                                          'TDew', 'black', 'degrees C')
            k_not_hist = plotting_functions.histogram_plot(self.k_not[~np.isnan(self.k_not)],
                                                           'Ko', 'black', 'degrees C')

            output_file(self.folder_path + "/correction_files/histograms/" + self.station_name + '_histograms.html',
                        title=self.station_name + ' histograms')

            save(gridplot([ws_hist, tmax_hist, tmin_hist, tavg_hist, tdew_hist, k_not_hist], ncols=2,
                          width=400, height=400, toolbar_location=None))

        #########################
        # Generate bokeh composite plot
        # Creates one large plot featuring all variables as subplots, used to get a concise overview of the full dataset
        # If user opts to not correct data (sets script_mode = 0), then this plots data before correction
        # If user does correct data, then this plots data after correction
        print("\nSystem: Now creating composite bokeh graph.")
        if self.generate_bokeh:  # Flag to create graphs or not
            plot_list = []
            x_size = 2000
            y_size = 3500

            if self.script_mode == 0:
                output_file(self.folder_path + "/correction_files/before_graphs/" + self.station_name +
                            "_before_corrections_composite_graph.html")
            elif self.script_mode == 1:
                output_file(self.folder_path + "/correction_files/after_graphs/" + self.station_name +
                            "_after_corrections_composite_graph.html")
            else:
                # Incorrect setup of script mode variable, raise an error
                raise ValueError('Incorrect parameters: script mode is not set to a valid option.')

            # Temperature Maximum and Minimum Plot
            plot_tmax_tmin = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_tmax,
                                                          self.data_tmin, 1, '')
            plot_list.append(plot_tmax_tmin)
            # Temperature Minimum and Dewpoint Plot
            plot_tmin_tdew = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_tmin,
                                                          self.data_tdew, 2, '', plot_tmax_tmin)
            plot_list.append(plot_tmin_tdew)

            # 'Completed' vapor pressure plot
            plot_comp_ea = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.compiled_ea, self.data_null,
                                                        7, 'Composite ', plot_tmax_tmin)
            plot_list.append(plot_comp_ea)

            # vapor pressure plot that was just the provided dataset
            if self.column_df.ea != -1:
                plot_data_ea = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_ea, self.data_null,
                                                            7, 'Provided ', plot_tmax_tmin)
                plot_list.append(plot_data_ea)

            # rh max and rh min plot if it was provided in dataset
            if self.column_df.rhmax != -1 and self.column_df.rhmin != -1:  # RH max and RH min
                plot_rhmax_rhmin = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_rhmax,
                                                                self.data_rhmin, 8, '', plot_tmax_tmin)
                plot_list.append(plot_rhmax_rhmin)

            # rh avg if it was provided in the dataset
            if self.column_df.rhavg != -1:  # RH Avg
                plot_rhavg = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_rhavg,
                                                          self.data_null, 9, '', plot_tmax_tmin)
                plot_list.append(plot_rhavg)

            # Mean Monthly Temperature Minimum and Dewpoint
            plot_mm_tmin_tdew = plotting_functions.line_plot(x_size, y_size, self.mm_dt_array, self.mm_tmin,
                                                             self.mm_tdew, 2, 'MM ')
            plot_list.append(plot_mm_tmin_tdew)

            # Mean Monthly k0 curve (Tmin-Tdew)
            plot_mm_k_not = plotting_functions.line_plot(x_size, y_size, self.mm_dt_array, self.mm_k_not,
                                                         self.data_null, 10, '', plot_mm_tmin_tdew)
            plot_list.append(plot_mm_k_not)

            # Solar radiation and clear sky solar radiation
            plot_rs_rso = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_rs, self.rso,
                                                       5, '', plot_tmax_tmin)
            plot_list.append(plot_rs_rso)

            # Windspeed
            plot_ws = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_ws, self.data_null,
                                                   3, '', plot_tmax_tmin)
            plot_list.append(plot_ws)

            # Precipitation
            plot_precip = plotting_functions.line_plot(x_size, y_size, self.dt_array, self.data_precip, self.data_null,
                                                       4, '', plot_tmax_tmin)
            plot_list.append(plot_precip)

            # Optimized mean monthly Thornton-Running solar radiation and Mean Monthly solar radiation
            plot_mm_opt_rs_tr = plotting_functions.line_plot(x_size, y_size, self.mm_dt_array, self.mm_rs,
                                                             self.mm_opt_rs_tr, 6, 'MM Optimized ', plot_mm_tmin_tdew)
            plot_list.append(plot_mm_opt_rs_tr)

            # Optimized mean monthly Thornton-Running solar radiation and Mean Monthly solar radiation
            plot_mm_orig_rs_tr = plotting_functions.line_plot(x_size, y_size, self.mm_dt_array, self.mm_rs,
                                                              self.mm_orig_rs_tr, 6, 'MM Original ', plot_mm_tmin_tdew)
            plot_list.append(plot_mm_orig_rs_tr)

            # Now construct grid plot out of all of the subplots
            number_of_plots = len(plot_list)
            number_of_rows = ceil(number_of_plots / self.gridplot_columns)

            grid_of_plots = [([None] * 1) for i in range(number_of_rows)]

            for i in range(number_of_rows):
                for j in range(self.gridplot_columns):

                    if len(plot_list) > 0:
                        grid_of_plots[i][j] = plot_list.pop(0)
                    else:
                        pass

            fig = gridplot(grid_of_plots, toolbar_location='left')
            fig.sizing_mode = 'scale_both'
            save(fig)

            print("\nSystem: Composite bokeh graph has been generated.")

    def _write_outputs(self):
        """
            Creates all the output files
        """

        #########################
        # Create necessary variables for generic metadata file, as well as
        # generate and fill metadata file
        record_start = pd.to_datetime(self.dt_array[0]).date()
        record_end = pd.to_datetime(self.dt_array[-1]).date()

        if self.script_mode == 1:  # only need to generate metadata if we are correcting it
            # First check to see if metadata file already exists
            if not os.path.isfile('correction_metadata.xlsx'):
                # file does not exist, create new one
                metadata_info = pd.DataFrame({'Station': self.station_name, 'Latitude': self.station_lat,
                                              'Longitude': self.station_lon, 'station_elev_m': self.station_elev,
                                              'record_start': record_start, 'record_end': record_end,
                                              'anemom_height_m': self.ws_anemometer_height,
                                              'Filename': self.output_file_path}, index=np.array([1]))

                with pd.ExcelWriter('correction_metadata.xlsx', date_format='YYYY-MM-DD',
                                    datetime_format='YYYY-MM-DD HH:MM:SS', engine='openpyxl', mode='w') as writer:
                    metadata_info.to_excel(writer, header=True,  index=False, sheet_name='Sheet1')
            else:
                # file is already created, so we need to read it in, append our new information to the bottom of it
                # and then save the info
                metadata_info = pd.read_excel('correction_metadata.xlsx', sheet_name=0, index_col=None,
                                              engine='openpyxl', keep_default_na=False, verbose=True)

                new_meta_info = pd.DataFrame({'Station': self.station_name, 'Latitude': self.station_lat,
                                              'Longitude': self.station_lon, 'station_elev_m': self.station_elev,
                                              'record_start': record_start, 'record_end': record_end,
                                              'anemom_height_m': self.ws_anemometer_height,
                                              'Filepath': self.output_file_path}, index=np.array([1]))

                output_metadata = pd.concat([metadata_info, new_meta_info], ignore_index=True)

                with pd.ExcelWriter('correction_metadata.xlsx', date_format='YYYY-MM-DD',
                                    datetime_format='YYYY-MM-DD HH:MM:SS', engine='openpyxl', mode='w') as writer:
                    output_metadata.to_excel(writer, header=True, index=False, sheet_name='Sheet1')

        else:
            # do nothing
            pass

        # if we are using a network-specific metadata file, we need to update the run count to pass it on
        if self.metadata_path is not None:
            current_row = self.metadata_df.run_count.ne(2).idxmax() - 1
            current_run = self.metadata_df.run_count.iloc[current_row] + 1

            self.metadata_df.run_count.iloc[current_row] = current_run
            self.metadata_df.record_start.iloc[current_row] = record_start
            self.metadata_df.record_end.iloc[current_row] = record_end
            self.metadata_df.output_path.iloc[current_row] = self.output_file_path

            with pd.ExcelWriter(self.metadata_path, date_format='YYYY-MM-DD',
                                datetime_format='YYYY-MM-DD', engine='openpyxl', mode='w') as writer:
                self.metadata_df.to_excel(writer, header=True, index=True, sheet_name='Sheet1')

        #########################
        # Generate output file
        # Create any final variables, then create panda dataframes to save all the data
        # Includes the following sheets:
        #     Corrected Data : Actual corrected values
        #     Delta : Magnitude of difference between original data and corrected data
        #     Filled Data : Tracks which data points have been filled by script generated values instead of provided
        # Data that is provided and subsequently corrected by the script do not count as filled values.
        print("\nSystem: Saving corrected data to .xslx file.")

        # Create any individually-requested output data
        ws_2m = _wind_height_adjust(uz=self.data_ws, zw=self.ws_anemometer_height)

        # Create corrected-original delta numpy arrays
        diff_tavg = np.array(self.data_tavg - self.original_df.tavg)
        diff_tmax = np.array(self.data_tmax - self.original_df.tmax)
        diff_tmin = np.array(self.data_tmin - self.original_df.tmin)
        diff_tdew = np.array(self.data_tdew - self.original_df.tdew)
        diff_ea = np.array(self.data_ea - self.original_df.ea)
        diff_rhavg = np.array(self.data_rhavg - self.original_df.rhavg)
        diff_rhmax = np.array(self.data_rhmax - self.original_df.rhmax)
        diff_rhmin = np.array(self.data_rhmin - self.original_df.rhmin)
        diff_rs = np.array(self.data_rs - self.original_df.rs)
        diff_rs_tr = np.array(self.opt_rs_tr - self.orig_rs_tr)
        diff_rso = np.array(self.rso - self.original_df.rso)
        diff_ws = np.array(self.data_ws - self.original_df.ws)
        diff_precip = np.array(self.data_precip - self.original_df.precip)
        diff_etr = np.array(self.etr - self.original_df.etr)
        diff_eto = np.array(self.eto - self.original_df.eto)

        # Create k0 array to output values
        k_not_vals = np.zeros(self.data_length)
        k_not_vals[0:12] = self.mm_k_not[0:12]

        # Create datetime for output dataframe
        datetime_df = pd.DataFrame({'year': self.data_year, 'month': self.data_month, 'day': self.data_day})
        datetime_df = pd.to_datetime(datetime_df[['month', 'day', 'year']])

        # Create output dataframe
        output_df = pd.DataFrame({'year': self.data_year, 'month': self.data_month,
                                  'day': self.data_day, 'TAvg (C)': self.data_tavg, 'TMax (C)': self.data_tmax,
                                  'TMin (C)': self.data_tmin, 'TDew (C)': self.data_tdew,
                                  'Compiled Ea (kPa)': self.compiled_ea,
                                  'Vapor Pres (kPa)': self.data_ea, 'RHAvg (%)': self.data_rhavg,
                                  'RHMax (%)': self.data_rhmax, 'RHMin (%)': self.data_rhmin, 'Rs (w/m2)': self.data_rs,
                                  'Opt_Rs_TR (w/m2)': self.opt_rs_tr, 'Rso (w/m2)': self.rso,
                                  'Windspeed (m/s)': self.data_ws, 'Precip (mm)': self.data_precip,
                                  'ETr (mm)': self.etr, 'ETo (mm)': self.eto, 'ws_2m (m/s)': ws_2m},
                                 index=datetime_df)

        # Creating difference dataframe to track amount of correction
        delta_df = pd.DataFrame({'year': self.data_year, 'month': self.data_month,
                                 'day': self.data_day, 'TAvg (C)': diff_tavg, 'TMax (C)': diff_tmax,
                                 'TMin (C)': diff_tmin, 'TDew (C)': diff_tdew,
                                 'Vapor Pres (kPa)': diff_ea, 'RHAvg (%)': diff_rhavg, 'RHMax (%)': diff_rhmax,
                                 'RHMin (%)': diff_rhmin, 'Rs (w/m2)': diff_rs, 'Opt - Orig Rs_TR (w/m2)': diff_rs_tr,
                                 'Rso (w/m2)': diff_rso, 'Windspeed (m/s)': diff_ws, 'Precip (mm)': diff_precip,
                                 'ETr (mm)': diff_etr, 'ETo (mm)': diff_eto}, index=datetime_df)

        # Creating a fill dataframe that tracks where missing data was filled in
        fill_df = pd.DataFrame({'year': self.data_year, 'month': self.data_month,
                                'day': self.data_day, 'TMax (C)': self.fill_tmax, 'TMin (C)': self.fill_tmin,
                                'TDew (C)': self.fill_tdew, 'Vapor Pres (kPa)': self.fill_ea, 'Rs (w/m2)': self.fill_rs,
                                'Complete Record Rso (w/m2)': self.fill_rso, 'mm k0 values': k_not_vals},
                               index=datetime_df)
        output_df.index.name = 'date'
        delta_df.index.name = 'date'
        fill_df.index.name = 'date'
        # Open up pandas excel writer
        output_writer = pd.ExcelWriter(self.output_file_path, engine='xlsxwriter')
        # Convert data frames to xlsxwriter excel objects
        output_df.to_excel(output_writer, sheet_name='Corrected Data', na_rep=self.missing_fill_value)
        delta_df.to_excel(output_writer, sheet_name='Delta (Corr - Orig)', na_rep=self.missing_fill_value)
        fill_df.to_excel(output_writer, sheet_name='Filled Data', na_rep=self.missing_fill_value)
        # Save output file
        output_writer.save()

        logger = open(self.log_file, 'a')
        if self.script_mode == 1 and self.fill_mode == 1:
            if np.isnan(self.eto).any() or np.isnan(self.etr).any():
                print("\nSystem: After finishing corrections and filling data, "
                      "ETr and ETo still had missing observations.")
                logger.write('After finishing corrections and filling data, '
                             'ETr and ETo still had missing observations. \n')
            else:
                logger.write('The output file for this station has a complete record of ETo and ETr observations. \n')
        else:
            pass
        logger.write('\nThe file has been successfully processed and output files saved at %s.' %
                     dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.close()

    def process_station(self):
        self._obtain_data()
        self._calculate_secondary_vars()
        self._correct_data()
        self._create_plots()
        self._write_outputs()


# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
