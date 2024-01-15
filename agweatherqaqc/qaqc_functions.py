import numpy as np
import math
import datetime as dt
import logging as log
import agweatherqaqc.plot as plotting_functions
from agweatherqaqc.utils import get_int_input, get_float_input, FEATURES_DICT
import warnings

from bokeh.plotting import save, show


def additive_corr(log_writer, start, end, var_one, var_two):
    """
    Corrects provided interval with a flat, user-provided additive modifier obtained via the CLI

    Args:
        :log_writer: Wrapper for writing to log file.
        :start: (int) starting index of correction interval.
        :end: (int) ending index of correction interval.
        :var_one: (ndarray) 1-D array of first variable.
        :var_two: (ndarray) 1-D array of second variable, may be entirely NaN.

    Returns:
        :corr_var_one: (ndarray) 1-D array of first variable after correction.
        :corr_var_two: (ndarray) 1-D array of second variable after correction, may be entirely NaN.
    """
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    mod = get_float_input("\nEnter the additive modifier you want to apply to all values: ")
    corr_var_one[start:end] = var_one[start:end] + mod
    corr_var_two[start:end] = var_two[start:end] + mod
    log_writer.write('Selected correction interval started at %s and ended at %s. \n' % (start, end))
    log_writer.write('Additive modifier applied for this interval was %s. \n' % mod)

    return corr_var_one, corr_var_two


def _generate_corr_menu(code, auto_corr, first_pass):
    """
    Generates menu and obtains user selection on how they want to correct the variables they have provided

    Args:
        :code: (int) integer code passed by main script that indicates what type of data has been passed
        :auto_corr: (bool) flag for whether automatic correction has been enabled
        :first_pass: (bool) flag for if this is the first iteration of correction or not

    Returns:
        :choice: (int) integer of user selection on how they want to correct data
        :first_pass: (bool) flag for if this is the first iteration of correction or not
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

    if auto_corr != 0 and first_pass == 1:  # automatic pass enabled
        choice = 4
        first_pass = 0
        print('\n Automatic first-pass correction is being performed, option 4 selected. \n')
    else:
        choice = get_int_input(1, 4, "Enter your selection: ")

    return choice, first_pass


def generate_interval(var_size):
    """
    Generates menu and obtains user selection on what intervals the user wants to correct via the CLI

    Args:
        :var_size: (int) of input data size, to prevent creation of an out of bound index

    Returns:
        :int_start: (int) of index user wants to start correction on
        :int_end: (int) of index user wants to end correction on
    """
    print('\nPlease enter the starting index of your correction interval.'
          '\n   You may also enter -1 to select all data points.')

    int_start = get_int_input(-1, var_size, 'Enter your starting index: ')
    if int_start == -1:
        int_start = 0
        int_end = var_size
    else:
        # get ending of interval, add two to ensure at least some data is corrected
        int_end = get_int_input(int_start+2, var_size, 'Enter your ending index: ')
        # Check that user didn't select past the end of record.
        if int_end > var_size:
            int_end = var_size
        else:
            pass
    # Check that int_end isn't before int_start
    if int_start > int_end:
        temp_end = int_end
        int_end = int_start
        int_start = temp_end
    return int_start, int_end


def multiplicative_corr(log_writer, start, end, var_one, var_two):
    """
    Corrects provided interval with a user-provided multiplicative modifier obtained from the CLI

    Args:
        :log_writer: Wrapper for writing to log file
        :start: (int) starting index of correction interval
        :end: (int) ending index of correction interval
        :var_one: (ndarray) 1-D numpy array of first variable
        :var_two: (ndarray) 1-D numpy array of second variable, may be entirely nan's
    Returns:
        :corr_var_one: (ndarray) 1-D array of first variable after correction
        :corr_var_two: (ndarray) 1-D array of second variable after correction, may be entirely nan's
    """
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    mod = get_float_input("\nEnter the multiplicative modifier you want to apply to all values: ")
    corr_var_one[start:end] = var_one[start:end] * mod
    corr_var_two[start:end] = var_two[start:end] * mod
    log_writer.write('Selected correction interval started at %s and ended at %s. \n' % (start, end))
    log_writer.write('Multiplicative modifier applied for this interval was %s. \n' % mod)

    return corr_var_one, corr_var_two


def set_to_nan(log_writer, start, end, var_one, var_two):
    """
    Sets entire provided interval to nans, likely because the observations are bad and need to be thrown out.

    Args:
        :log_writer: Wrapper for writing to log file
        :start: (int) starting index of correction interval
        :end: (int) ending index of correction interval
        :var_one: (ndarray) 1-D array of first variable
        :var_two: (ndarray) 1-D array of second variable, may be entirely nan's

    Returns:
        :corr_var_one: (ndarray) 1-D array of first variable after data was removed
        :corr_var_two: (ndarray) 1-D array of second variable after data was removed, may be entirely nan's
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

    Args:
        :data: (ndarray) 1-D array of values

    Returns:
        :cleaned_data: (ndarray) 1-D array of values that have had outliers removed
        :outlier_count: (int) number of outliers removed
    """
    threshold = 3.5
    cleaned_data = np.array(data)

    median = np.nanmedian(data)
    median_absolute_deviation = np.nanmedian([np.abs(x - median) for x in data])
    modified_z_scores = np.array([0.6745 * (x - median) / median_absolute_deviation for x in data])

    warnings.filterwarnings('ignore', 'invalid value encountered')  # catch invalid value warning for nans in data
    removed_indices = np.array(np.where(np.abs(modified_z_scores) > threshold))  # array of indices for zscore > thresh
    warnings.resetwarnings()  # reset warning filter to default

    cleaned_data[removed_indices] = np.nan  # set those indices to nan
    outlier_count = removed_indices.size
    return cleaned_data, outlier_count


def temp_find_outliers(log_writer, var_one, var_one_name, var_two, var_two_name, month):
    """
    Wrapper function for modified_z_score_outlier_detection() that will process provided temperature variables.
    Due to seasonal variation in temperature the overall temperature record is subset into months
    (ex. all January observations are grouped together) and modified_z_score_outlier_detection() is run 12 times.

    Args:
        :log_writer: Wrapper for writing to log file
        :var_one: (ndarray) 1-D array of first variable, either tmax, or tmin
        :var_one_name: (str) name for var one
        :var_two: (ndarray) 1-D array of second variable, either tmin or tdew
        :var_two_name: (str) name for var two
        :month: (ndarray) 1-D array of month values

    Returns:
        :corrected_var_one: (ndarray) 1-D array of first variable after data was removed
        :corrected_var_two: (ndarray) 1-D array of second variable after data was removed

    """
    log_writer.write('User has opted to use a modified z-score approach to identify and remove outliers. \n')
    var_one_total_outliers = 0
    var_two_total_outliers = 0

    corrected_var_one = np.array(var_one)
    corrected_var_two = np.array(var_two)

    k = 1
    while k <= 12:
        t_index = np.where(month == k)[0]

        (corrected_var_one[t_index], var_one_outlier_count) = modified_z_score_outlier_detection(var_one[t_index])
        (corrected_var_two[t_index], var_two_outlier_count) = modified_z_score_outlier_detection(var_two[t_index])

        var_one_total_outliers = var_one_total_outliers + var_one_outlier_count
        var_two_total_outliers = var_two_total_outliers + var_two_outlier_count
        k += 1

    # check to make sure TMin isn't getting double-corrected
    if var_one_name == "Temperature Minimum":
        # Tmin/Tdew correction option
        print('Temperature Minimum is corrected as part of Temperature Maximum / Temperature Minimum.')
        log_writer.write('Temperature Minimum is corrected as part of Temperature Maximum / Temperature Minimum.')
        print('{0} outliers were removed on variable {1}.'.format(var_two_total_outliers, var_two_name))
        log_writer.write('{0} outliers were removed on variable {1}. \n'
                         .format(var_two_total_outliers, var_two_name))

        return var_one, corrected_var_two
    else:
        # Tmax/Tmin correciton option
        print('{0} outliers were removed on variable {1}.'.format(var_one_total_outliers, var_one_name))
        log_writer.write('{0} outliers were removed on variable {1}. \n'
                         .format(var_one_total_outliers, var_one_name))
        print('{0} outliers were removed on variable {1}.'.format(var_two_total_outliers, var_two_name))
        log_writer.write('{0} outliers were removed on variable {1}. \n'
                         .format(var_two_total_outliers, var_two_name))
        return corrected_var_one, corrected_var_two


def rh_yearly_percentile_corr(log_writer, start, end, rhmax, rhmin, year, percentage):
    """
    Performs a year-based percentile correction on relative humidity, works on the assumption that,
    in areas with significant agriculture, every year should have at least a few observations
    where RHMax hits 100% (such as when it rains). This is a concise way to solve sensor drift issues that may arise.
    The correction strength is determined only by RHMax values, but the correction is also applied to RHMin values
    as they are obtained by the same sensor and likely suffer the same sensor drift problem.

    Args:
        :log_writer: Wrapper for writing to log file
        :start: (int) starting index of correction interval
        :end: (int) ending index of correction interval
        :rhmax: (ndarray) 1-D array of rhmax values
        :rhmin: (ndarray) 1-D array of rhmin
        :year: (ndarray) 1-D array of year values
        :percentage: (int) what top yearly percentage of observations user wants to base correction on

    Returns:
        :corr_rhmax: (ndarray) 1-D array of rhmax values after correction is applied
        :corr_rhmin: (ndarray) 1-D array of rhmin values after correction is applied
    """

    # Obtain sample size from percentage value provided
    percentage_sample_size = np.floor(100/percentage)
    # ID unique years in data set
    unique_years = np.unique(year)
    corr_sample_per_year = np.zeros(unique_years.size)
    rh_corr_per_year = np.zeros(unique_years.size)

    corr_rhmax = np.array(rhmax)
    corr_rhmin = np.array(rhmin)

    for k in range(unique_years.size):
        t_index = np.where(year == unique_years[k])[0]
        t_index = np.array(t_index)

        rh_year = np.array(rhmax[t_index])
        rh_year = rh_year[~np.isnan(rh_year)]

        # find the required number of days to sample each year by dividing the size of the year by percent_sample_size
        corr_sample_per_year[k] = int(np.floor((rh_year.size / percentage_sample_size)))
        if corr_sample_per_year[k] < 1:
            corr_sample_per_year[k] = 1
        else:
            pass

        rh_year_sorted = rh_year.argsort()
        rh_values_to_pull = int(corr_sample_per_year[k])
        rh_sample_indexes = rh_year_sorted[-rh_values_to_pull:]
        rh_corr_per_year[k] = 100 / np.nanmean(rh_year[rh_sample_indexes])

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
    invert_max_min_cutoff = 0  # tracks the number of times RHmax was less than RHmin (as an initial problem w/ data)
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
        elif corr_rhmax[i] <= 0:  # This should never really happen but need to control for it anyway.
            corr_rhmax[i] = 1
        else:
            pass

        if corr_rhmin[i] > 100:
            corr_rhmin[i] = 100
            rhmin_cutoff += 1
        elif corr_rhmin[i] <= 0:  # This should never really happen but need to control for it anyway
            corr_rhmin[i] = 1
        else:
            pass

        if corr_rhmax[i] < corr_rhmin[i]:
            corr_rhmax[i] = np.nan
            corr_rhmin[i] = np.nan
            invert_max_min_cutoff += 1
        else:
            pass

    print("\n" + str(rhmax_cutoff) + " RHMax data points were removed for exceeding the logical limit of 100%.")
    print("\n" + str(rhmin_cutoff) + " RHMin data points were removed for exceeding the logical limit of 100%.")
    print("\n" + str(invert_max_min_cutoff) + " indexes were removed because RHMax was less than RHMin.")
    log_writer.write('Year-based RH correction used the top %s percentile (%s points for a full year), '
                     'RHMax had %s points exceed 100 percent.'
                     ' RHMin had %s points exceed 100 percent. \n'
                     % (percentage, int(np.floor((365 / percentage_sample_size))), rhmax_cutoff, rhmin_cutoff))

    return corr_rhmax, corr_rhmin


def rs_period_ratio_corr(log_writer, start, end, rs, rso, sample_size_per_period, period):
    """
    This function corrects rs by applying a correction factor (a ratio of clear-sky solar radiation (rso) over
    observed solar radiation (rs)) to each user defined period to counteract sensor drift and other errors.

    The start and end of the correction interval is used to cut a section of both rs and rso,
    with these new sections being divided into user-defined periods. Each period then has a correction factor
    calculated based on the user-specified largest number of points for rs/rso.
    Averages are formed for both rs and rso of those largest points, and then this average rso
    is divided by this average rs to get a final ratio, which multiplied to all points within its corresponding period.

    Within each period, the code checks for the existence of potential isolated erroneous readings
    (electrical shorts, datalogger errors, etc.), which it does by looking at how the correction factor
    changes by shifting which values are included.

    The logic here being that erroneous values generally appear as a "spike" of Rs that is significantly
    higher than Rso, which would heavily influence the correction factor due to it being the ratio of averages.

    The existence of these "spikes" is evaluated numerically. We have the original correction factor of the
    six largest rs/rso ratios, and we compute it again by dropping the largest ratio and including the next
    largest. Ex: 1st-6th largest would become 2nd-7th largest. We check to see if this shifted in included
    values causes a larger than 2% change in the correction factor, and if so this whole process is repeated
    until the correction factor doesn't significantly change. Values determined to be bad are set to
    a marker value and then later set to be equal to Rso * 1.05.

    Example:
        sorted_ratio_list = [2, 1.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7...]

        Correction factor doesn't change significantly when computed between values 3rd-8th and 4th-9th

        Correction factor that will be applied to the data will be based on values 3rd-8th, and the values for
        1st and 2nd will set equal to the corresponding Rso values * 1.05 after the data is corrected

    If a period does not contain enough valid data points to fill the user-specified number, the entire period
    is thrown out. To prevent the code from correcting data beyond the point of believability, if the correction
    factor is below 0.5 or above 1.5, the data for that period is removed instead.

    In addition, if the correction factor is between 0.97 < X < 1.03, the data is unchanged under the assumption
    that the sensor was behaving as expected.

    Finally, the function returns the corrected solar radiation that has had erroneous readings removed (if applicable)
    and the period-based correction factor applied. Post-correction Rs data that exceeds Rso by 3% is clipped to Rso.

    Args:
        :log_writer: Wrapper for writing to the log file
        :start: (int) starting index of correction interval
        :end: (int) ending index of correction interval
        :rs: (ndarray) 1-D numpy array of rs
        :rso: (ndarray) 1-D numpy array of rso
        :sample_size_per_period: (int) number of points in each period correction factors are calculated with
        :period: (int) length of each correction period within the user-specified interval

    Returns:
        :corr_rs: (ndarray) 1-D array of corrected rs values
        :rso: (ndarray) 1-D array, not actually changed, is returned for consistent behavior in main qaqc function.
    """

    corr_rs = np.array(rs)  # corrected variable that all the corrections are going to be written to
    insufficient_period_counter = 0  # counter for the number of periods that were removed due to insufficient data
    insufficient_data_counter = 0  # counter for the number of rs data points that were removed due to insufficient data
    bad_vals_counter = 0  # counter for bad vals like voltage shorts, datalogger errors, etc.

    # Determining correction factor for intervals based on pre-defined periods
    num_periods = int(math.ceil((end - start) / period))
    rs_period = np.zeros(period)
    rso_period = np.zeros(period)
    period_corr = np.zeros(num_periods)

    # Placing intervals in separate array for easy handling
    rs_interval = np.array(rs[start:end])
    rso_interval = np.array(rso[start:end])
    cleaned_rs_interval = np.array([])  # used to recreate interval of rs that will track the removal of bad obs

    # separate the interval into predefined periods and compute correction
    interval_index = 0  # index for full correction interval
    within_period_index = 0  # index for within each period
    num_period_index = 0  # index for number of periods
    while interval_index < len(rs_interval):

        # If statement to handle being at the end of the period, or at the end of the overall correction interval
        if ((within_period_index < period) and interval_index == len(rs_interval) - 1) or within_period_index == period:

            if within_period_index < period:  # We are dealing with the final period
                rs_period[within_period_index] = rs_interval[interval_index]
                rso_period[within_period_index] = rso_interval[interval_index]

                # each period's data is overwritten by the subsequent period's data, because the final period may not
                # have 60 days, chop off remaining days that have values from previous period.
                rs_period = rs_period[:within_period_index-(period-1)].copy()
                rso_period = rso_period[:within_period_index-(period-1)].copy()
                interval_index += 1  # increment by 1 to end the loop after this iteration
            else:  # We have reached the end of a period, no special treatment needed
                pass

            # Now that we are at the end of a period or finishing up the last period,
            # we check for the existence of potential bad values
            period_ratios = np.divide(rs_period, rso_period)
            period_ratios_copy = np.array(period_ratios)  # make a copy, we remove largest val to find the next largest
            max_ratio_indexes = []  # tracks the indexes of the maximum values found

            invalid_period = 0  # boolean flag to specify if this period has the data necessary to calculate corr factor
            bad_vals_loop = 1  # boolean flag to specify if we should keep checking for bad values or not

            # First, check to see if there are non-nan values present
            # and the period has at least the sample size in days present
            # and pull the 6 largest ratios to serve as the initial correction factor.
            if np.any(np.isfinite(period_ratios_copy)) and np.size(period_ratios_copy) >= sample_size_per_period:
                for i in range(sample_size_per_period):  # loop through and return enough largest non nan values
                    max_ratio_indexes.append(np.nanargmax(period_ratios_copy))
                    period_ratios_copy[np.nanargmax(period_ratios_copy)] = np.nan  # set to nan to find next largest

                    if np.any(np.isfinite(period_ratios_copy)):  # are any non-nan values still present?
                        # Yes, continue to find next largest value
                        pass
                    else:
                        # only nans are left, have to quit loop and throw out the data
                        invalid_period = 1
                        bad_vals_loop = 0
                        print('\nA period was thrown out due to insufficient data, failed finding valid point # %s '
                              ' out of the required %s.' % (i + 1, sample_size_per_period))
                        break
            else:
                # there is not enough data in this final period to compute correction data
                print('\nA period was thrown out due to insufficient data, either because it had no valid ratios,'
                      'or because it had less than %s days.' % sample_size_per_period)
                invalid_period = 1
                bad_vals_loop = 0

            # Start a loop that remains true as long as none of the ending conditions are met while iterating down
            # the rest of the values until reasonably sure that remaining points don't massively shift the data
            cf_index_start = 0
            cf_index_end = cf_index_start + sample_size_per_period  # ending index is not inclusive
            new_cf_index_start = cf_index_start + 1
            new_cf_index_end = cf_index_end + 1
            while bad_vals_loop == 1:

                if np.any(np.isfinite(period_ratios_copy)) and np.size(period_ratios_copy) >= sample_size_per_period:
                    max_ratio_indexes.append(np.nanargmax(period_ratios_copy))
                    period_ratios_copy[np.nanargmax(period_ratios_copy)] = np.nan  # set to nan to find next largest

                else:
                    # only nans are left, end the loop and set the period as invalid
                    # this is under the logic that if we've iterated through all points without finding a
                    # value that seems okay then something is obviously wrong with this period.
                    invalid_period = 1
                    bad_vals_loop = 0
                    print('\nA period was thrown out due to failing to find a sufficient '
                          'number of valid values when testing for bad values.')

                rs_avg = np.nanmean(rs_period[max_ratio_indexes[cf_index_start:cf_index_end]])
                rso_avg = np.nanmean(rso_period[max_ratio_indexes[cf_index_start:cf_index_end]])

                new_rs_avg = np.nanmean(rs_period[max_ratio_indexes[new_cf_index_start:new_cf_index_end]])
                new_rso_avg = np.nanmean(rso_period[max_ratio_indexes[new_cf_index_start:new_cf_index_end]])

                # Example: if current_cf uses largest points 0-5, new_cf uses largest points 1-6 (omitting the largest)
                current_cf = rso_avg / rs_avg  # current correction factor from currently used points
                new_cf = new_rso_avg / new_rs_avg  # exploratory correction factor used to check for large changes
                diff_cf = new_cf - current_cf
                percent_diff_cf = (diff_cf / current_cf) * 100

                # First of the two rules used to check for the existence of bad values, the logic is that if
                # removing the largest point causes over a 2% change in the correction factor (which is an average of
                # six largest points) then that point carried an undue influence and is a likely bad value
                # We only need to care if Rs_average is above Rso_average
                if percent_diff_cf >= 2.0 and rs_avg > rso_avg:
                    new_cf_significant_change = True
                else:
                    new_cf_significant_change = False

                # Second of the two rules used to check for the existence of bad values is if Rs average
                # is sufficiently larger than rso average. This would occur with many  bad values with consistent values
                # this should occur very infrequently
                if (rs_avg - rso_avg) >= 75:
                    rs_avg_greatly_exceeds_rso_avg = True
                else:
                    rs_avg_greatly_exceeds_rso_avg = False

                # Now we see if either of the two rules were violated
                if new_cf_significant_change or rs_avg_greatly_exceeds_rso_avg:
                    # at least one of the rules were violated, so continue forward with the next iteration

                    # check for the rarer rule occurring:
                    if not new_cf_significant_change and rs_avg_greatly_exceeds_rso_avg:
                        print('\nWARNING: The rule for rs greatly exceeding rso was triggered without triggering the'
                              ' significant change to correction factor rule. Look at the data to make sure the data'
                              ' has a lot of bad values. Period was {} starting around {} and ending around {}. \n'
                              .format(num_period_index, (interval_index - period), interval_index))

                    # increment indexes and keep iterating for more bad values
                    cf_index_start += 1
                    cf_index_end = cf_index_start + sample_size_per_period  # ending index is not inclusive
                    new_cf_index_start = cf_index_start + 1
                    new_cf_index_end = cf_index_end + 1

                    bad_vals_counter += 1
                else:
                    # if neither of the two rules were violated, we can proceed with the assumption that all likely
                    # bad values have been removed, and we use the current_cf as the correction factor
                    bad_vals_loop = 0

            if invalid_period != 1:  # period has valid data to compute correction factor
                rs_avg = np.nanmean(rs_period[max_ratio_indexes[cf_index_start:cf_index_end]])
                rso_avg = np.nanmean(rso_period[max_ratio_indexes[cf_index_start:cf_index_end]])

                period_corr[num_period_index] = rso_avg / rs_avg  # compute the correction factor

                # Go through and set the rs points marked as likely bad values to a unique identifier to find later
                rs_period[max_ratio_indexes[:cf_index_start]] = -12345

            else:
                # This period has insufficient data to correct, instead we will remove all points and track how many we
                # remove
                removed_points = np.count_nonzero(~np.isnan(rs_period))  # count number of points we're about to remove
                rs_period[:] = np.nan  # insufficient data exists to correct this period, so set it to nan
                period_corr[num_period_index] = np.nan
                insufficient_period_counter += 1
                insufficient_data_counter += removed_points
                print('\nThis insufficient period contained %s datapoints for Rs, which have been set to nan.'
                      % removed_points)

            # add this period's rs data, which has had potentially bad values removed, to the new interval of rs
            cleaned_rs_interval = np.append(cleaned_rs_interval, rs_period)

            # adjust counters to move to next period, if this is the final period then does nothing.
            within_period_index = 0
            num_period_index += 1

        elif within_period_index < period:
            # haven't run out of data points, and period still hasn't been filled
            rs_period[within_period_index] = rs_interval[interval_index]
            rso_period[within_period_index] = rso_interval[interval_index]
            interval_index += 1
            within_period_index += 1

        else:
            # This should never happen
            pass

    # Now that the correction factor has been computed for each period, we now step through each period again and
    # apply those correction factors
    corr_rs[start:end] = cleaned_rs_interval[:]  # save all the values removed for suspect values/insufficient data
    correction_cutoff_counter = 0
    rso_clipping_counter = 0
    unchanged_data_counter = 0
    x = start  # index that tracks along data points for the full selected correction interval
    y = 0  # index that tracks how far along a period we are
    z = 0  # index that tracks which correction period we are in
    while x < len(rs) and x < end and z < len(period_corr):
        # x is less than the length of var1 to prevent OOB,
        # and is before or at the end of the correction interval,
        # and we have not yet run out of correction periods
        # and capping correction by a fifty percent increase or decrease
        if y <= period:
            # if y is less than the size of a correction period

            # Check to see if rs correction factor is smaller than a 50% relative increase or decrease
            # if it is larger than that we will remove it for a later fill with Rs_TR
            if 0.50 <= period_corr[z] <= 1.50:

                # was the current rs point removed for being a potentially bad value?
                # if so, set it to 1.05*Rso and leave it there (do not later clip it)
                if corr_rs[x] == -12345:
                    corr_rs[x] = rso[x] * 1.05

                else:
                    if 0.97 <= period_corr[z] <= 1.03:
                        # don't change the data under the assumption that the sensor is working
                        unchanged_data_counter += 1
                    else:
                        # apply the correction to the data
                        corr_rs[x] = rs[x] * period_corr[z]

                    if corr_rs[x] > (rso[x] * 1.03):  # Check to see if Rs now sufficiently exceeds rso for clipping
                        corr_rs[x] = rso[x]
                        rso_clipping_counter += 1
                    else:  # no special action needed
                        pass

            elif np.isnan(period_corr[z]):
                # This data was already set to nan during the steps above, so pass
                pass
            else:
                # correction factor would be too high, so throw out the data
                corr_rs[x] = np.nan
                correction_cutoff_counter += 1
            x += 1
            y += 1
        else:
            # We have reached the end of the correction period, go to next period
            y = 1
            z += 1

    print('\n%s data points were removed as part of the suspect values evaluation process. \n' % bad_vals_counter)
    print('\n%s Rs data points were removed due to their correction factor exceeding a '
          '50 percent relative increase or decrease. \n' % correction_cutoff_counter)

    print('\n%s Rs data points in %s different periods were removed due to insufficient data present in either Rs or '
          'Rso to compute a correction factor. \n' % (insufficient_data_counter, insufficient_period_counter))

    print('\n%s Rs data points were clipped to Rso due to exceeding 1.03 * Rso after correction.'
          % rso_clipping_counter)

    print('\n%s Rs data points were unchanged due to the correction factor being between 0.97 and 1.03.'
          % unchanged_data_counter)

    log_writer.write('Periodic ratio-based Rs corrections were applied,'
                     ' period length was %s, and correction sample size was %s. \n'
                     % (period, sample_size_per_period))
    log_writer.write('%s data points were removed as part of the suspect value evaluation process. \n'
                     % bad_vals_counter)
    log_writer.write('%s Rs data points in %s different periods were removed due to insufficient data present in'
                     ' either Rs or Rso to compute a correction factor. \n'
                     % (insufficient_data_counter, insufficient_period_counter))
    log_writer.write('%s data points were removed due to their correction factor exceeding a '
                     '50 percent relative increase or decrease. \n' % correction_cutoff_counter)
    log_writer.write('\n%s Rs data points were clipped to  1.03 * Rso due to exceeding 1.03 * Rso after correction.'
                     % rso_clipping_counter)

    return corr_rs, rso


def correction(station, log_path, folder_path, var_one, var_two, dt_array, month, year, code, auto_corr=0):
    """
    This main qaqc function takes in two variables and, depending on the code provided, enables different
    correction methods for the user to use to correct data. This function serves as the
    wrapper/handler for all other correction method functions. Once a correction has been applied, user has the
    option to do multiple iterations before finishing. All actions taken are recorded into the log file.

    After each iteration a bokeh graph is generated that shows the changes that have occurred. After the user
    decides to completely finish with corrections, one final bokeh plot is generated that shows the final
    corrected product vs the uncorrected data that was initially passed in

    Args:
        :station: (str) station name for saving files
        :log_path: (str) path to log file
        :folder_path: (str) path to correction files directory
        :var_one: (ndarray) 1-D numpy array of first variable passed
        :var_two: (ndarray) 1-D numpy array of second variable, may be all NaN
        :dt_array: (ndarray) 1-D datetime array used for bokeh plotting
        :month: (ndarray) 1-D numpy array of month values
        :year: (ndarray) 1-D numpy array of year values
        :code: (int) used to determine what variables are actually passed as var_one and var_two
        :auto_corr: (int) flag for the "automatic first pass" mode, which auto-applies default correction first

    Returns:
        :corr_var_one: (ndarray) 1-D numpy array of corrected var_one values
        :corr_var_two: (ndarray) 1-D numpy array of corrected var_two values
    """
    correction_loop = 1
    first_pass = 1  # boolean flag for whether it is the first pass, used in automation with auto_corr
    var_size = var_one.shape[0]
    backup_var_one = np.array(var_one)
    backup_var_two = np.array(var_two)
    corr_var_one = np.array(var_one)
    corr_var_two = np.array(var_two)

    ####################
    # Reopen log file and append correction actions taken to it.
    log.basicConfig()
    corr_log = open(log_path, 'a')
    if FEATURES_DICT[code]['var_two_name'] is None:
        corr_log.write('\n\nCorrecting %s at %s. \n'
                       % (FEATURES_DICT[code]['var_one_name'], dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    else:
        corr_log.write('\n\nCorrecting %s and %s at %s. \n'
                       % (FEATURES_DICT[code]['var_one_name'], FEATURES_DICT[code]['var_two_name'],
                          dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    ####################
    # Generate Before-Corrections Graph
    if first_pass == 1 and auto_corr != 0:  # first automatic pass, skip plotting variables for now
        pass
    else:
        corr_fig = plotting_functions.variable_correction_plots(station, dt_array, var_one, corr_var_one, var_two,
                                                                corr_var_two, code, folder_path)
        show(corr_fig)

    ####################
    # Correction Loop
    # Give the user as many iterations to do corrections as they wish
    while correction_loop:
        ####################
        # Interval and Correction Method Selection
        # Determine what subset of data the user wants to correct, then determine how they want to do it.

        if first_pass == 1 and auto_corr != 0:  # first automatic pass, select full bracket
            int_start = 0
            int_end = var_size
        else:
            (int_start, int_end) = generate_interval(var_size)

        (choice, first_pass) = _generate_corr_menu(code, auto_corr, first_pass)

        if choice == 1:
            (corr_var_one, corr_var_two) = additive_corr(corr_log, int_start, int_end, var_one, var_two)
        elif choice == 2:
            (corr_var_one, corr_var_two) = multiplicative_corr(corr_log, int_start, int_end, var_one, var_two)
        elif choice == 3:
            (corr_var_one, corr_var_two) = set_to_nan(corr_log, int_start, int_end, var_one, var_two)
        elif choice == 4 and (code == 1 or code == 2):
            (corr_var_one, corr_var_two) = temp_find_outliers(corr_log, var_one, FEATURES_DICT[code]['var_one_name'],
                                                              var_two, FEATURES_DICT[code]['var_two_name'], month)
        elif choice == 4 and code == 8:
            if auto_corr != 0:
                corr_percentile = 1
            else:
                corr_percentile = get_int_input(
                    1, 365,
                    '\nEnter which top percentile you want to base corrections on (rec. 1): ')

            (corr_var_one, corr_var_two) = rh_yearly_percentile_corr(corr_log, int_start, int_end, var_one, var_two,
                                                                     year, corr_percentile)
        elif choice == 4 and code == 5:
            if auto_corr != 0:
                corr_period = 60
                corr_sample = 6
            else:
                corr_period = get_int_input(
                    1, 365,
                    '\nEnter the number of days each correction period will last (rec. 60): ')
                corr_sample = get_int_input(
                    1, corr_period,
                    '\nEnter the number of points per period to correct based on (rec 6): ')

            (corr_var_one, corr_var_two) = rs_period_ratio_corr(corr_log, int_start, int_end, var_one, var_two,
                                                                corr_sample, corr_period)

        elif choice == 4 and (code == 3 or code == 4 or code == 7 or code == 9):
            # Data is either uz, precip, ea, or rhavg and user doesn't want to correct it.
            corr_log.write('Selected correction interval started at %s and ended at %s. \n' % (int_start, int_end))
            corr_log.write('User decided to skip this interval without correcting it. \n')
        else:
            # Shouldn't happen, raise an error
            raise ValueError('Unsupported code type {0} and choice type {1} passed to qaqc_functions.'
                             .format(code, choice))

        # Generate After-Corrections Graph
        corr_fig = plotting_functions.variable_correction_plots(station, dt_array, var_one, corr_var_one, var_two,
                                                                corr_var_two, code, folder_path)
        show(corr_fig)

        if auto_corr == 1 or auto_corr == 0:
            auto_corr = 0  # set to 0 to prevent another automatic correction loop

        # Determine if user wants to keep correcting
        print('\nAre you done correcting?'
              '\n   Enter 1 for yes.'
              '\n   Enter 2 for another iteration.'
              '\n   Enter 3 to start over.'
              '\n   Enter 4 to discard all changes.')

        choice = get_int_input(1, 4, "Enter your selection: ")

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
                                                            backup_var_two, corr_var_two, code, folder_path)
    save(corr_fig)

    # return corrected variables, or save original values as corrected values if correction was rejected
    corr_log.close()
    return corr_var_one, corr_var_two


def compiled_humidity_adjustment(station, log_path, folder_path, dt_array, tmax, tmin, tavg, compiled_ea, ea, ea_col,
                                 tdew, tdew_col, tdew_ko, rhmax, rhmax_col, rhmin, rhmin_col, rhavg, rhavg_col):
    """
    This function displays the 'compiled' ea generated from all available humidity data, and the user will have
    the option to overwrite sections of the 'compiled' ea with ea generated from a variable of their choice, should
    a higher priority humidity variable have worse data than a lower priority one.

    Example 1: 
        A station has both vapor pressure (daily average calculated from 15 minute intervals)
        and RH Maximum and Minimum (daily values). The humidity compilation function will only use RHMax and RHMin
        to calculate vapor pressure if there is a gap in the provided vapor pressure data. However, for some reason the
        vapor pressure data is bad, either from a faulty sensor or problem with the sampling, while the contemporaneous
        RH data is good. This function will allow you to graphically select the 'bad' section of vapor pressure data
        and overwrite it with the vapor pressure calculated from the present RH Maximum and minimum data.
        
    Example 2: 
        A station has both vapor pressure (daily average calculated from 15 minute intervals)
        and RH Maximum and Minimum (daily values). Data from all variables is bad for the periods of 01/2016-12/2016.
        This function would allow you to fill in the 'compiled' ea values from 2016 with values from Tmin - Ko 

    Args:
        :station: (str) station name for saving files
        :log_path: (str) path to log file
        :folder_path: (str) path to correction files directory
        :dt_array: (ndarray) 1-D datetime array used for bokeh plots
        :tmax: (ndarray) 1-D array of maximum temperature values
        :tmin: (ndarray) 1-D array of minimum temperature values
        :tavg: (ndarray) 1-D array of average temperature values
        :compiled_ea: (ndarray) the array of ea values that has been generated from all provided humidity variables
        :ea: (ndarray) 1-D array of vapor pressure values, which may be empty
        :ea_col: (int) used to determine if ea was provided by the data source
        :tdew: (ndarray) 1-D array of dewpoint temperature values, which may be empty
        :tdew_col: (int) column of Tdew variable in data file, if it is provided
        :tdew_ko: (ndarray) 1-D array of dewpoint temperature values, where missing values are filled in by Tmin-Ko curve
        :rhmax: (ndarray) 1-D array of maximum relative humidity values, which may be empty
        :rhmax_col: (int) column of rhmax variable in data file, if it was provided
        :rhmin: (ndarray) 1-D array of minimum relative humidity values, which may be empty
        :rhmin_col: (int) column of rhmin variable in data file, if it was provided
        :rhavg: (ndarray) 1-D array of average relative humidity values, which may be empty
        :rhavg_col: (int) column of rhavg variable in data file, if it was provided
    Returns:
        :edited_compiled_ea: (ndarray) ea array that has had selected sections replaced by the selected sources
    """

    adjustment_loop = 1
    var_size = compiled_ea.shape[0]
    backup_compiled_ea = np.array(compiled_ea)
    edited_compiled_ea = np.array(compiled_ea)

    ####################
    # Logging
    # Reopen log file and append correction actions taken to it.
    log.basicConfig()
    humidity_log = open(log_path, 'a')
    humidity_log.write('\n------------------------------------------------------------------------------------------\n')
    humidity_log.write('Now beginning humidity record adjustment. \n')

    humidity_fig = (
        plotting_functions.humidity_adjustment_plots(station, dt_array, edited_compiled_ea, ea, ea_col, tmin,
                                                     tdew, tdew_col, rhmax, rhmax_col, rhmin, rhmin_col,
                                                     rhavg, rhavg_col, tdew_ko, folder_path))
    show(humidity_fig)

    ####################
    # Adjustment Loop
    # User gets to repeat this process as many times as they want
    while adjustment_loop:

        ####################
        # First the user will select an interval, then they will choose a variable to copy from.
        (int_start, int_end) = generate_interval(var_size)

        print('\nPlease select which variable you want to use for this interval:'
              '\n   To use Ea data provided by the input file, enter 1.'
              '\n   To use Dewpoint Temperature data provided by the input file, enter 2.'
              '\n   To use RH Max and Min data provided by the input file, enter 3.'
              '\n   To use RH Avg data provided by the input file, enter 4.'
              '\n   To use Dewpoint temperature data that was filled in from TMin - Ko, enter 5.'
              '\n   To skip this selected interval, enter 6.')

        choice = get_int_input(1,6, "Enter your selection: ")
        loop = 1

        while loop:
                if choice == 1 and ea_col == -1:
                    print('Ea was not provided by the dataset, please select a provided option.')
                    choice = get_int_input(1,6, 'Specify which variable you would like to use: ')
                elif choice == 2 and tdew_col == -1:
                    print('TDew was not provided by the dataset, please select a provided option.')
                    choice = get_int_input(1,6, 'Specify which variable you would like to use: ')
                elif choice == 3 and (rhmax_col == -1 or rhmin_col == -1):
                    print('RH Max and Min were not provided by the dataset, please select a provided option.')
                    choice = get_int_input(1,6, 'Specify which variable you would like to use: ')
                elif choice == 4 and rhavg_col == -1:
                    print('RH Avg was not provided by the dataset, please select a provided option.')
                    choice = get_int_input(1,6, 'Specify which variable you would like to use: ')
                else:
                    # Ko Tdew and skipping always a possible option
                    loop = 0

        humidity_log.write('Selected interval started at %s and ended at %s. \n' % (int_start, int_end))

        if choice == 1:
            # User wants provided Ea
            edited_compiled_ea[int_start:int_end] = ea[int_start:int_end]
            print('\n The selected interval was overwritten by provided vapor pressure.')
            humidity_log.write('Variable used was provided vapor pressure. \n')

        elif choice == 2:
            # User wants provided TDew
            s_tdew = tdew[int_start:int_end]  # Selected interval of tdew
            calc_ea = np.array(0.6108 * np.exp((17.27 * s_tdew) / (s_tdew + 237.3)))  # EQ 8, units kPa
            edited_compiled_ea[int_start:int_end] = calc_ea
            print('\n The selected interval was overwritten by provided dewpoint temperature.')
            humidity_log.write('Variable used was provided dewpoint temperature. \n')

        elif choice == 3:
            # User wants provided RHMax and RHMin
            s_tmax = tmax[int_start:int_end]
            s_tmin = tmin[int_start:int_end]
            s_rhmax = rhmax[int_start:int_end]
            s_rhmin = rhmin[int_start:int_end]

            eo_tmax = np.array(0.6108 * np.exp((17.27 * s_tmax) / (s_tmax + 237.3)))  # units kPa, EQ 7
            eo_tmin = np.array(0.6108 * np.exp((17.27 * s_tmin) / (s_tmin + 237.3)))  # units kPa, EQ 7
            calc_ea = np.array(((eo_tmin * (s_rhmax / 100)) + (eo_tmax * (s_rhmin / 100))) / 2)  # EQ 11
            edited_compiled_ea[int_start:int_end] = calc_ea
            print('\n The selected interval was overwritten by RH Maximum and Minimum.')
            humidity_log.write('Variable used was provided RH Maximum and Minimum. \n')

        elif choice == 4:
            # User wants provided RHAvg
            s_tavg = tavg[int_start:int_end]
            s_rhavg = rhavg[int_start:int_end]

            eo_tavg = np.array(0.6108 * np.exp((17.27 * s_tavg) / (s_tavg + 237.3)))  # units kPa, EQ 7
            calc_ea = np.array(eo_tavg * (s_rhavg / 100))  # EQ 14
            edited_compiled_ea[int_start:int_end] = calc_ea
            print('\n The selected interval was overwritten by RH Average.')
            humidity_log.write('Variable used was provided RH Average. \n')

        elif choice == 5:
            # User wants provided TDew that was completed by Tmin-Ko curve
            s_tdew_ko = tdew_ko[int_start:int_end]  # Selected interval of tdew
            calc_ea = np.array(0.6108 * np.exp((17.27 * s_tdew_ko) / (s_tdew_ko + 237.3)))  # EQ 8, units kPa
            edited_compiled_ea[int_start:int_end] = calc_ea
            print('\n The selected interval was overwritten by dewpoint temperature filled in with the k0 curve.')
            humidity_log.write('Variable used was provided dewpoint temperature filled in by the Ko curve. \n')

        elif choice == 6:
            print('\n The selected interval was not modified.')
            humidity_log.write('The selected interval was skipped. \n')

        else:
            # Incorrect choice was passed, raise an error
            raise ValueError('Incorrect parameters: CHOICE in humidity adjustment was an unexpected value.')

        # Now that the section has been overwritten, replot the variables
        humidity_fig = (
            plotting_functions.humidity_adjustment_plots(station, dt_array, edited_compiled_ea, ea, ea_col, tmin,
                                                         tdew, tdew_col, rhmax, rhmax_col, rhmin, rhmin_col,
                                                         rhavg, rhavg_col, tdew_ko, folder_path))
        show(humidity_fig)

        ####################
        # Determine if user wants to keep correcting
        print('\nAre you done adjusting humidity?'
              '\n   Enter 1 for yes.'
              '\n   Enter 2 for another iteration.'
              '\n   Enter 3 to start over.'
              '\n   Enter 4 to discard all changes.')

        choice = get_int_input(1,6, "Enter your selection: ")

        if choice == 1:
            adjustment_loop = 0
            humidity_log.write('---> User has elected to end adjustments. \n')
        elif choice == 2:
            humidity_log.write('---> User has elected to do another iteration of adjustments. \n')
        elif choice == 3:
            edited_compiled_ea = np.array(backup_compiled_ea)
            humidity_log.write('---> User has elected to ignore previous iterations of adjustments and start over. \n')
        else:
            adjustment_loop = 0
            edited_compiled_ea = np.array(backup_compiled_ea)
            humidity_log.write('---> User has elected to end adjustments without keeping any changes. \n')

    humidity_log.close()
    return edited_compiled_ea


# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
