import numpy as np
import math
import datetime as dt
import logging as log
from . import plotting_functions

from bokeh.plotting import save, show


def additive_corr(log_writer, start, end, var_one, var_two):
    """
        Corrects provided interval with a flat, user-provided additive modifier

        Parameters:
            log_writer : logging object for log file
            start : starting index of correction interval
            end : ending index of correction interval
            var_one : 1D numpy array of first variable
            var_two : 1D numpy array of second variable, may be entirely nan's

        Returns:
            corr_var_one : 1D numpy array of first variable after correction
            corr_var_two : 1D numpy array of second variable after correction, may be entirely nan's

    """
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    mod = float(input("\nEnter the additive modifier you want to apply to all values: "))
    corr_var_one[start:end] = var_one[start:end] + mod
    corr_var_two[start:end] = var_two[start:end] + mod
    log_writer.write('Selected correction interval started at %s and ended at %s. \n' % (start, end))
    log_writer.write('Additive modifier applied for this interval was %s. \n' % mod)

    return corr_var_one, corr_var_two


def generate_corr_menu(code):
    """
        Generates menu and obtains user selection on how they want to correct the variables they have provided

        Parameters:
            code : integer code passed by main script that indicates what type of data has been passed

        Returns:
            choice : integer of user selection on how they want to correct data

    """
    corr_method = '\n   To skip correcting this data, enter 4.'

    # code value is unordered here but matches what is expected by plotting functions
    if code == 1 or code == 2:
        var_type = 'temperature'
        corr_method = '\n   Use MM averages to determine outliers and fill in missing data, enter 4 (Recommended).'
    elif code == 3:
        var_type = 'wind speed'
    elif code == 4:
        var_type = 'precipitation'
    elif code == 5:
        var_type = 'solar radiation'
        corr_method = '\n   To correct based on periodic percentile intervals, enter 4 (Recommended).'
    elif code == 7:
        var_type = 'vapor pressure'
    elif code == 8:
        var_type = 'relative humidity'
        corr_method = '\n   To correct based on yearly percentiles, enter 4 (Recommended).'
    else:
        raise ValueError('Unsupported code type {} passed to qaqc_functions.'.format(code))

    print('\nPlease select the method to use to correct this {} data:'
          '\n   For user-defined additive value correction, enter 1.'
          '\n   For user-defined multiplicative value correction, enter 2.'
          '\n   To set everything in this interval to NaN, enter 3.'.format(var_type))
    print(corr_method)

    choice = int(input("Enter your selection: "))
    loop = 1

    while loop:
        if 1 <= choice <= 4 and 1 <= code <= 3:
            loop = 0
        else:
            print('Please enter a valid option.')
            choice = int(input('Specify which variable you would like to correct: '))

    return choice


def generate_interval(var_size):
    """
        Generates menu and obtains user selection on what intervals the user wants to correct

        Parameters:
            var_size : integer of variable size, to prevent creation of an out of bound index

        Returns:
            int_start : integer of index user wants to start correction on
            int_end : integer of index user wants to end correction on
    """
    print('\nPlease enter the starting index of your correction interval.'
          '\n   You may also enter -1 to select all data points.')

    int_start = int(input("Enter your starting index: "))
    if int_start == -1:
        int_start = 0
        int_end = var_size
    else:
        int_end = int(input("Enter your ending index: "))
        # Check that user didn't select past the end of record.
        if int_end > var_size:
            int_end = var_size
        else:
            pass
    return int_start, int_end


def multiplicative_corr(log_writer, start, end, var_one, var_two):
    """
        Corrects provided interval with a user-provided multiplicative modifier

        Parameters:
            log_writer : logging object for log file
            start : starting index of correction interval
            end : ending index of correction interval
            var_one : 1D numpy array of first variable
            var_two : 1D numpy array of second variable, may be entirely nan's

        Returns:
            corr_var_one : 1D numpy array of first variable after correction
            corr_var_two : 1D numpy array of second variable after correction, may be entirely nan's

    """
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    mod = float(input("\nEnter the multiplicative modifier you want to apply to all values: "))
    corr_var_one[start:end] = var_one[start:end] * mod
    corr_var_two[start:end] = var_two[start:end] * mod
    log_writer.write('Selected correction interval started at %s and ended at %s. \n' % (start, end))
    log_writer.write('Multiplicative modifier applied for this interval was %s. \n' % mod)

    return corr_var_one, corr_var_two


def set_to_nan(log_writer, start, end, var_one, var_two):
    """
        Sets entire provided interval to nans, likely because the observations are bad and need to be thrown out.

        Parameters:
            log_writer : logging object for log file
            start : starting index of correction interval
            end : ending index of correction interval
            var_one : 1D numpy array of first variable
            var_two : 1D numpy array of second variable, may be entirely nan's

        Returns:
            corr_var_one : 1D numpy array of first variable after data was removed
            corr_var_two : 1D numpy array of second variable after data was removed, may be entirely nan's

    """
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    corr_var_one[start:end] = np.nan
    corr_var_two[start:end] = np.nan
    log_writer.write('Selected correction interval started at %s and ended at %s. \n' % (start, end))
    log_writer.write('Observations within the interval were set to nan.')

    return corr_var_one, corr_var_two


def rs_percent_corr(start, end, rs, rso, thresh, period):
    # TODO: finish commenting out this function
    # TODO: replace math with np
    # Determining percentile correction for intervals based on pre-defined periods
    num_periods = int(math.ceil((end - start) / period))
    rs_period = np.zeros(period)
    rso_period = np.zeros(period)
    period_corr = np.zeros(num_periods)

    # Placing intervals in separate array for easy handling
    rs_interval = np.array(rs[start:end])
    rso_interval = np.array(rso[start:end])

    # separate the interval into predefined periods and compute correction
    count_one = 0  # index for full correction interval
    count_two = 0  # index for within each period
    count_three = 0  # index for number of periods
    while count_one < len(rs_interval):
        if (count_two < period) and count_one == len(rs_interval) - 1:
            # if statement handles final period
            rs_period[count_two] = rs_interval[count_one]
            rso_period[count_two] = rso_interval[count_one]
            count_one += 1
            count_two += 1
            while count_two < period:
                # This fills out the rest of the final period with NaNs so
                # they are not impacted by the remaining zeros
                rs_period[count_two] = np.nan
                rso_period[count_two] = np.nan
                count_two += 1

            ratio = np.divide(rs_period, rso_period)
            period_corr[count_three] = np.nanpercentile(ratio, thresh)

        elif count_two < period:
            # haven't run out of data points, and period still hasn't been filled
            rs_period[count_two] = rs_interval[count_one]
            rso_period[count_two] = rso_interval[count_one]
            count_one += 1
            count_two += 1
        else:
            # end of a period
            count_two = 0
            ratio = np.divide(rs_period, rso_period)
            period_corr[count_three] = np.nanpercentile(ratio, thresh)
            count_three += 1

    return period_corr


# correct given data using method chosen by user
def correction(station, log_path, var_one, var_one_name, var_two, var_two_name, dt_array, mon, yr, code):
    # station - string name of station path for saving correction graphs
    # var1 - values of first variable passed
    # var1n - name of first var passed as string
    # var2 - values of second variable passed
    # var2n - name of second var passed as string, or "NULL" if only 1 var
    # dates - datetime structure
    # month - vector of months
    # yr - vector of years
    # code - integer that tells the type of data that has been passed in, and what correction methods can be applied
    #       1 for temperature data
    #       2 for RH
    #       3 for Rs
    #       4 for windspeed or precipitation data
    correction_loop = 1
    var_size = var_one.shape[0]
    backup_var_one = np.array(var_one)
    backup_var_two = np.array(var_two)
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    ####################
    # Logging
    # Reopen log file and append correction actions taken to it.
    log.basicConfig()
    corr_log = open(log_path, 'a')
    corr_log.write('----------------------------------------------------------------------------------------------- \n')
    corr_log.write('Now correcting %s and %s at %s. \n' %
                   (var_one_name, var_two_name, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    ####################
    # Generate Before-Corrections Graph
    corr_fig = plotting_functions.variable_correction_plots(station, dt_array, var_one, corr_var_one, var_two,
                                                            corr_var_two, code)
    show(corr_fig)

    ####################
    # Correction Loop
    # Give the user as many iterations to do corrections as they wish
    while correction_loop:
        ####################
        # Interval and Correction Method Selection
        # Determine what subset of data the user wants to correct, then determine how they want to do it.
        (int_start, int_end) = generate_interval(var_size)
        choice = generate_corr_menu(code)

        if choice == 1:
            (corr_var_one, corr_var_two) = additive_corr(corr_log, int_start, int_end, var_one, var_two)
        elif choice == 2:
            (corr_var_one, corr_var_two) = multiplicative_corr(corr_log, int_start, int_end, var_one, var_two)
        elif choice == 3:
            (corr_var_one, corr_var_two) = set_to_nan(corr_log, int_start, int_end, var_one, var_two)
        elif choice == 4 and (code == 1 or code == 2):
            # TODO temp correction
            pass
        elif choice == 4 and code == 8:
            # todo rhmax/min correction
            pass
        elif choice == 4 and code == 5:
            # TODO rs correction
            pass
        elif choice == 4 and (code == 4 or code == 5 or code == 7):
            # Data is either ea, uz, or precip and user doesn't want to correct it.
            corr_log.write('Selected correction interval started at %s and ended at %s. \n' % (int_start, int_end))
            corr_log.write('User decided to pass over this interval without correcting it. \n')
        else:
            # Shouldn't happen, raise an error
            raise ValueError('Unsupported code type {0} and choice type {1} passed to qaqc_functions.'
                             .format(code, choice))

        ####################
        # Generate After-Corrections Graph
        corr_fig = plotting_functions.variable_correction_plots(station, dt_array, var_one, corr_var_one, var_two,
                                                                corr_var_two, code)
        show(corr_fig)

        ####################
        # Determine if user wants to keep correcting
        print('\nAre you done correcting?'
              '\n   Enter 1 for yes.'
              '\n   Enter 2 for another iteration.'
              '\n   Enter 3 to start over.'
              '\n   Enter 4 to discard all changes.')

        choice = int(input("Enter your selection: "))
        loop = 1
        while loop:
            if 1 <= choice <= 4:
                loop = 0
            else:
                print('Please enter a valid option.')
                choice = int(input('Enter your selection: '))

        if choice == 1:
            correction_loop = 0
            corr_log.write('---> User has elected to end corrections. \n\n')
        elif choice == 2:
            var_one = np.array(corr_var_one)
            var_two = np.array(corr_var_two)
            corr_log.write('---> User has elected to do another iteration of corrections. \n\n')
        elif choice == 3:
            var_one = np.array(backup_var_one)
            var_two = np.array(backup_var_two)
            corr_var_one = np.array(backup_var_one)
            corr_var_two = np.array(backup_var_two)
            corr_log.write('---> User has elected to ignore previous iterations of corrections and start over. \n\n')
        else:
            correction_loop = 0
            corr_var_one = np.array(backup_var_one)
            corr_var_two = np.array(backup_var_two)
            corr_log.write('---> User has elected to end corrections without keeping any changes. \n\n')

    ####################
    # Generate Final Graph
    # All previous graphs were either entirely before corrections, or showed differences between iterations
    # This graph is between completely original values and final corrected product
    corr_fig = plotting_functions.variable_correction_plots(station, dt_array, backup_var_one, corr_var_one,
                                                            backup_var_two, corr_var_two, code)
    save(corr_fig)

    # return corrected variables, or save original values as corrected values if correction was rejected
    corr_log.close()
    return corr_var_one, corr_var_two


# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
