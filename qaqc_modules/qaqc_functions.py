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
    corr_method = '   To skip correcting this data, enter 4.'

    # code value is unordered here but matches what is expected by plotting functions
    if code == 1 or code == 2:
        var_type = 'temperature'
        corr_method = '   To remove outliers using a modified z-score approach, enter 4 (Recommended).'
    elif code == 3:
        var_type = 'wind speed'
    elif code == 4:
        var_type = 'precipitation'
    elif code == 5:
        var_type = 'solar radiation'
        corr_method = '   To correct based on periodic percentile intervals, enter 4 (Recommended).'
    elif code == 7:
        var_type = 'vapor pressure'
    elif code == 8:
        var_type = 'relative humidity'
        corr_method = '   To correct based on yearly percentiles, enter 4 (Recommended).'
    elif code == 9:
        var_type = 'relative humidity'
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
        if 1 <= choice <= 4:
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
    log_writer.write('Observations within the interval were set to nan. \n')

    return corr_var_one, corr_var_two


def modified_z_score_outlier_detection(data):
    """
        Calculates the modified z scores of provided dataset and sets to nan any values that are above the threshold
        The modified z approach and threshold of 3.5 is recommended in:

        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and Handle Outliers",
        The ASQC Basic References in Quality Control: Statistical Techniques

        Modified z scores are more robust than traditional z scores because they are determined by the median, which is
        less susceptible to outliers.

    Parameters:
        data : 1D numpy array of values, most likely temperature values for a given month

    Returns:
        cleaned_data : 1D numpy array of values that have had outliers removed
        outlier_count : integer of number of outliers removed
    """
    threshold = 3.5
    cleaned_data = np.array(data)

    median = np.nanmedian(data)
    median_absolute_deviation = np.nanmedian([np.abs(x - median) for x in data])
    modified_z_scores = np.array([0.6745 * (x - median) / median_absolute_deviation for x in data])

    np.warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning for nans in data
    removed_indices = np.array(np.where(np.abs(modified_z_scores) > threshold))  # array of indices for zscore > thresh
    np.warnings.resetwarnings()  # reset warning filter to default

    cleaned_data[removed_indices] = np.nan  # set those indices to nan
    outlier_count = removed_indices.size
    return cleaned_data, outlier_count


def temp_find_outliers(log_writer, var_one, var_one_name, var_two, var_two_name, month):
    """
            Uses a modified z-score approach to automatically detect outliers and set them to nan.

            Parameters:
                log_writer : logging object for log file
                var_one : 1D numpy array of first variable, either tmax, or tmin
                var_one_name : string of var one name
                var_two : 1D numpy array of second variable, either tmin or tdew
                var_two_name : string of var two name
                month : 1D numpy array of month values

            Returns:
                var_one : 1D numpy array of first variable after data was removed
                var_two : 1D numpy array of second variable after data was removed

    """
    log_writer.write('User has opted to use a modified z-score approach to identify and remove outliers. \n')
    var_one_total_outliers = 0
    var_two_total_outliers = 0

    k = 1
    while k <= 12:
        t_index = np.where(month == k + 1)[0]
        t_index = np.array(t_index)

        (var_one[t_index], var_one_outlier_count) = modified_z_score_outlier_detection(var_one[t_index])
        (var_two[t_index], var_two_outlier_count) = modified_z_score_outlier_detection(var_two[t_index])

        var_one_total_outliers = var_one_total_outliers + var_one_outlier_count
        var_two_total_outliers = var_two_total_outliers + var_two_outlier_count
        k += 1

    print('{0} outliers were removed on variable {1}.'.format(var_one_total_outliers, var_one_name))
    print('{0} outliers were removed on variable {1}.'.format(var_two_total_outliers, var_two_name))
    log_writer.write('{0} outliers were removed on variable {1}. \n'.format(var_one_total_outliers, var_one_name))
    log_writer.write('{0} outliers were removed on variable {1}. \n'.format(var_two_total_outliers, var_two_name))

    return var_one, var_two


def rh_yearly_percentile_corr(log_writer, start, end, rhmax, rhmin, year):
    """
            Performs a year-based percentile correction on relative humidity, works on the belief that every year should
            have at least a few observations where RHMax hits 100% (such as when it rains). This is a concise way to
            solve sensor drift issues that may arise. The correction strength is determined only by RHMax values, but
            the correction is also duplicated to RHMin values as they are obtained by the same sensor and likely suffer
            the same sensor drift problem.

            Parameters:
                log_writer : logging object for log file
                start : starting index of correction interval
                end : ending index of correction interval
                rhmax : 1D numpy array of rhmax
                rhmin : 1D numpy array of rhmin
                year : 1D numpy array of year values

            Returns:
                corr_rhmax : 1D numpy array of rhmax values after correction is applied
                corr_rhmin : 1D numpy array of rhmin values after correction is applied

    """
    # Corrects the data based on a year-based percentile correction
    corr_thresh = float(input("\nEnter the percentile threshold to use for this correction (rec. 98-99): "))

    # ID unique years in data set
    unique_years = np.unique(year)
    percentile_year = np.zeros(unique_years.size)
    rh_corr_per_year = np.zeros(unique_years.size)
    corr_rhmax = np.array(rhmax)
    corr_rhmin = np.array(rhmin)

    for k in range(unique_years.size):
        t_index = np.where(year == unique_years[k])[0]
        t_index = np.array(t_index)

        rh_year = np.array(rhmax[t_index])
        percentile_year[k] = np.nanpercentile(rh_year, corr_thresh)
        rh_corr_per_year[k] = 100 / percentile_year[k]

        print("{0} days were included in year {1} of the RH correction process."
              .format(rh_year.size, unique_years[k]))

    # Check to see if the years are lined up, Ex. data file starts in 2001 but correction starts in 2004
    offset = 0
    if start != 0:  # If the start of the interval is at 0 then we're already lined up
        align_bool = 1
        while align_bool == 1:
            if year[start] != unique_years[offset]:
                offset += 1
            else:
                align_bool = 0
    else:
        pass

    # Now we apply the correction to both RHmax and RHmin
    rhmax_cutoff = 0  # tracks number of observations corrected above 100%
    rhmin_cutoff = 0  # tracks number of observations corrected above 100%
    for i in range(start, end):
        if unique_years[offset] == year[i]:  # Years are aligned
            corr_rhmax[i] = rhmax[i] * rh_corr_per_year[offset]
            corr_rhmin[i] = rhmin[i] * rh_corr_per_year[offset]
        else:
            # Encountered last day of year, increment to next correction year and continue
            offset += 1
            corr_rhmax[i] = rhmax[i] * rh_corr_per_year[offset]
            corr_rhmin[i] = rhmin[i] * rh_corr_per_year[offset]

        # Check for corrected values exceeding 100%
        if corr_rhmax[i] > 100:
            corr_rhmax[i] = 100
            rhmax_cutoff += 1
        elif corr_rhmax[i] < 0:  # This should never really happen but need to control for it anyways.
            corr_rhmax[i] = 0
        else:
            pass

        if corr_rhmin[i] > 100:
            corr_rhmin[i] = 100
            rhmin_cutoff += 1
        elif corr_rhmin[i] < 0:  # This should never really happen but need to control for it anyways
            corr_rhmin[i] = 0
        else:
            pass

    print("\n" + str(rhmax_cutoff) + " RHMax data points were removed for exceeding the logical limit of 100%.")
    print("\n" + str(rhmin_cutoff) + " RHMin data points were removed for exceeding the logical limit of 100%.")

    log_writer.write('Year-based RH correction used the %s th percentile, RHMax had %s points exceed 100 percent.'
                     ' RHMin had %s points exceed 100 percent. \n'
                     % (corr_thresh, rhmax_cutoff, rhmin_cutoff))
    return corr_rhmax, corr_rhmin


def rs_percent_corr(start, end, rs, rso, thresh, period):
    """
            This function is called by rs_period_percentile_corr(), takes in both rs and rso, calculates the
            percentile correction factor for each period, and returns an array of those factors

            Parameters:
                start : starting index of correction interval
                end : ending index of correction interval
                rs : 1D numpy array of rs
                rso : 1D numpy array of rso
                thresh : percentile threshold that correction factors are going to be calculated off of
                period : length of each correction period within the user-specified interval

            Returns:
                period_corr : 1D numpy array of correction factors for each period within the interval

    """
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


def rs_period_percentile_corr(log_writer, start, end, rs, rso):
    """
            This corrects solar radiation by applying a percentile-based correction to each user-defined period
            also despikes the data by removing all potentially-erroneous spikes in rs values so that they do not impact
            the actual percentile correction.

            Parameters:
                log_writer : logging object for log file
                start : starting index of correction interval
                end : ending index of correction interval
                rs : 1D numpy array of rs
                rso : 1D numpy array of rso

            Returns:
                corr_rs : 1D numpy array of corrected rs values
                rso : not actually changed from input, but is returned to keep everything consistent in main qaqc funct.

    """
    corr_rs = np.array(rs)

    discard_thresh = float(input('\nEnter the discard threshold as a percentage integer (recommended 99): '))
    corr_period = int(input('\nEnter the number of days each correction period will last (rec. 60): '))
    corr_thresh = float(input('\nEnter the correction threshold as a percentage integer (recommended 90): '))

    # begin by despiking rs data, all values removed are set to NaN
    # this is done to ideally remove all/most observations that are the result of voltage spikes or bad readings
    # so that they do not impact the actual percentile correction
    despike_ratios = rs / rso
    despike_discard = np.nanpercentile(despike_ratios, discard_thresh)

    despike_counter = 0
    for i in range(start, end):
        if despike_ratios[i] > despike_discard:
            rs[i] = np.nan
            despike_counter += 1
        else:
            pass
    print("\n" + str(despike_counter) + " points were removed as part of the rs despiking procedure.")

    log_writer.write('Periodic Percentile Rs corrections were applied, despiking percentile was %s,'
                     ' period length was %s, and correction percentile was %s. \n'
                     % (discard_thresh, corr_period, corr_thresh))
    log_writer.write('%s data points were removed as part of the despiking process. \n'
                     % despike_counter)

    # now that data is despiked, correction can begin, pass to function to determine values for each period
    rs_corr_values = rs_percent_corr(start, end, rs, rso, corr_thresh, corr_period)  # correction factors to apply to rs

    # now apply those values to the data for each period
    x = start  # index that tracks along data points for the full selected correction interval
    y = 0  # index that tracks how far along a period we are
    z = 0  # index that tracks which correction period we are in
    while x < len(rs) and x < end and z < len(rs_corr_values):
        # x is less than the length of var1 to prevent OOB,
        # and is before or at the end of the correction interval
        # and we have not yet run out of correction periods
        if y <= corr_period:
            # if y is less than the size of a correction period
            corr_rs[x] = rs[x] / rs_corr_values[z]
            x += 1
            y += 1
        else:
            # We have reached the end of the correction period, go to next period
            y = 1
            z += 1

    return corr_rs, rso


def correction(station, log_path, var_one, var_two, dt_array, month, year, code):
    """
            This main qaqc function takes in two variables and, depending on the code provided, enables different
            correction methods for the user to use to correct data. Once a correction has been applied, user has the
            option to do multiple iterations before finishing. All actions taken are recorded into the log file.

            After each iteration a bokeh graph is generated that shows the changes that have occurred. After the user
            decides to completely finish with corrections, one final bokeh plot is generated that shows the final
            corrected product vs the uncorrected data that was initially passed in

            Parameters:
                station : string of station name for saving files
                log_path : string of path to log file
                var_one : 1d numpy array of first variable passed
                var_two : 1d numpy array of second variable passed
                dt_array : date time array used for bokeh plotting
                month : 1D numpy array of month values
                year : 1D numpy array of year values
                code : integer that is used to determine what variables are actually passed as var_one and var_two

            Returns:
                corr_var_one : 1D numpy array of corrected var_one values
                corr_var_two : 1D numpy array of corrected var_two values
    """
    correction_loop = 1
    var_size = var_one.shape[0]
    backup_var_one = np.array(var_one)
    backup_var_two = np.array(var_two)
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    (units, title, var_one_name, var_one_color, var_two_name, var_two_color) = \
        plotting_functions.generate_line_plot_features(code, '')

    ####################
    # Logging
    # Reopen log file and append correction actions taken to it.
    log.basicConfig()
    corr_log = open(log_path, 'a')
    corr_log.write('\n--------------------------------------------------------------------------------------------\n')
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
            (corr_var_one, corr_var_two) = temp_find_outliers(corr_log, var_one, var_one_name, var_two, var_two_name,
                                                              month)
        elif choice == 4 and code == 8:
            (corr_var_one, corr_var_two) = rh_yearly_percentile_corr(corr_log, int_start, int_end, var_one, var_two,
                                                                     year)
        elif choice == 4 and code == 5:
            (corr_var_one, corr_var_two) = rs_period_percentile_corr(corr_log, int_start, int_end, var_one, var_two)

        elif choice == 4 and (code == 3 or code == 4 or code == 7 or code == 9):
            # Data is either uz, precip, ea, or rhavg and user doesn't want to correct it.
            corr_log.write('Selected correction interval started at %s and ended at %s. \n' % (int_start, int_end))
            corr_log.write('User decided to skip this interval without correcting it. \n')
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
            corr_log.write('---> User has elected to end corrections. \n')
        elif choice == 2:
            var_one = np.array(corr_var_one)
            var_two = np.array(corr_var_two)
            corr_log.write('---> User has elected to do another iteration of corrections. \n')
        elif choice == 3:
            var_one = np.array(backup_var_one)
            var_two = np.array(backup_var_two)
            corr_var_one = np.array(backup_var_one)
            corr_var_two = np.array(backup_var_two)
            corr_log.write('---> User has elected to ignore previous iterations of corrections and start over. \n')
        else:
            correction_loop = 0
            corr_var_one = np.array(backup_var_one)
            corr_var_two = np.array(backup_var_two)
            corr_log.write('---> User has elected to end corrections without keeping any changes. \n')

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
