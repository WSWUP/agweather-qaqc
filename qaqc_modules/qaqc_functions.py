import numpy
import math
import random
import datetime as dt
import logging as log

from bokeh.layouts import gridplot
from bokeh.plotting import figure, output_file, reset_output, save, show


# called by correction function, corrects RS data based on percentile
def rs_percent_corr(start, end, rs, rso, thresh, period):

    # Determining percentile correction for intervals based on pre-defined periods
    num_periods = int(math.ceil((end - start) / period))
    rs_period = numpy.zeros(period)
    rso_period = numpy.zeros(period)
    period_corr = numpy.zeros(num_periods)

    # Placing intervals in separate array for easy handling
    rs_interval = numpy.array(rs[start:end])
    rso_interval = numpy.array(rso[start:end])

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
                rs_period[count_two] = numpy.nan
                rso_period[count_two] = numpy.nan
                count_two += 1

            ratio = numpy.divide(rs_period, rso_period)
            period_corr[count_three] = numpy.nanpercentile(ratio, thresh)

        elif count_two < period:
            # haven't run out of data points, and period still hasn't been filled
            rs_period[count_two] = rs_interval[count_one]
            rso_period[count_two] = rso_interval[count_one]
            count_one += 1
            count_two += 1
        else:
            # end of a period
            count_two = 0
            ratio = numpy.divide(rs_period, rso_period)
            period_corr[count_three] = numpy.nanpercentile(ratio, thresh)
            count_three += 1

    return period_corr


# correct given data using method chosen by user
def correction(station, log_path, var1, var1n, var2, var2n, dates, mon, yr, code):
    # station - string name of station path for saving correction graphs
    # var1 - values of first variable passed
    # var1n - name of first var passed as string
    # var2 - values of second variable passed
    # var2n - name of second var passed as string, or "NONE" if only 1 var
    # dates - datetime structure
    # month - vector of months
    # yr - vector of years
    # code - integer that tells the type of data that has been passed in, and what correction methods can be applied
    #       1 for temperature data
    #       2 for RH
    #       3 for Rs
    #       4 for windspeed or precipitation data
    log.basicConfig()

    # Reopen log file to append corrections
    corr_log = open(log_path, 'a')
    corr_log.write('----------------------------------------------------------------------------------------------- \n')
    corr_log.write('Now correcting %s and %s at %s. \n' %
                   (var1n, var2n, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    redo_loop = 1
    var2_flag = 1
    x_size = 800
    y_size = 350
    var_size = var1.shape[0]

    var1 = numpy.array(var1)
    var1.astype(float)
    backup_var1 = numpy.array(var1)
    backup_var1.astype(float)
    corr_var1 = numpy.array(var1)
    corr_var1.astype(float)

    var2 = numpy.array(var2)
    var2.astype(float)
    backup_var2 = numpy.array(var2)
    backup_var2.astype(float)
    corr_var2 = numpy.array(var2)
    corr_var2.astype(float)

    mon = numpy.array(mon)
    mon.astype(float)

    if var2n == 'NONE':
        title_string = var1n
        var2_flag = 0
    else:
        title_string = var1n + '_and_' + var2n

    # ############################################################################################
    # Generate Bokeh plot before correction so user can see what they're looking at.
    # I am drawing four subplots (three of which are blank) to keep visual consistency with final generated plot
    blank_var1 = numpy.array(var1)
    blank_var1[:] = numpy.nan
    blank_var2 = numpy.array(var2)
    blank_var2[:] = numpy.nan

    reset_output()  # clears bokeh output, prevents ballooning file sizes
    output_file(station + "_" + title_string + "_correction_graph.html")
    cs1 = figure(
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' Original',
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    cs1.line(dates, backup_var1, line_color="black", legend="Original " + var1n)
    if var2_flag == 1:
        cs1.line(dates, backup_var2, line_color="blue", legend="Original " + var2n)
    else:
        pass
    cs1.legend.location = "bottom_left"

    cs2 = figure(
        x_range=cs1.x_range,
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' Corrected',
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    # Showing a nan for this plot because no corrections have occurred yet
    cs2.line(dates, blank_var1, line_color="black", legend="Corrected " + var1n)

    if var2_flag == 1:
        # Showing a nan for this plot because no corrections have occurred yet
        cs2.line(dates, blank_var2, line_color="blue", legend="Corrected " + var2n)
    else:
        pass
    cs2.legend.location = "bottom_left"

    cs3 = figure(
        x_range=cs1.x_range,
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' Deltas',
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    cs3.line(dates, corr_var1 - blank_var1, line_color="black", legend="Delta of " + var1n)
    if var2_flag == 1:
        cs3.line(dates, corr_var2 - blank_var2, line_color="blue", legend="Delta of " + var2n)
    else:
        pass
    cs3.legend.location = "bottom_left"

    cs4 = figure(
        x_range=cs1.x_range,
        width=x_size, height=y_size, x_axis_type="datetime",
        x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' % Difference',
        tools='pan, box_zoom, undo, reset, hover, save'
    )
    cs4.line(dates, blank_var1, line_color="black", legend="% Difference of " + var1n)
    if var2_flag == 1:
        cs4.line(dates, blank_var2, line_color="blue", legend="% Difference of " + var2n)
    else:
        pass
    cs4.legend.location = "bottom_left"

    corrfig = gridplot([[cs1], [cs2], [cs3], [cs4]], toolbar_location="left")
    show(corrfig)

    while redo_loop == 1:

        # #############################################################################################
        # User will be asked for a series of data points to define intervals
        # Data points will be pulled using bokeh graphs from the first mode
        # user can enter in 'f' for full data series

        # section three will be all ratios of corr/original data, to determine what % of data was corrected

        print('\nPlease enter the starting index of your correction interval.'
              '\n   You may also enter -1 to select all data points.'
              )

        int_start = int(input("Enter your starting index: "))
        if int_start == -1:
            int_start = 0
            int_end = var1.shape[0]
        else:
            int_end = int(input("Enter your ending index: "))
            if int_end > var_size:
                int_end = var_size
            else:
                pass

        corr_log.write('Selected correction interval started at %s and ended at %s. \n' % (int_start, int_end))

        # ##############################################################################################
        # Available correction methods are dependant on variables passed

        # Temperature data
        if code == 1:

            print('\nPlease select the method to use to correct this temperature data:'
                  '\n   For user-defined additive value correction, enter 1.'
                  '\n   For user-defined multiplicative value correction, enter 2.'
                  '\n   To set everything in this interval to NaN, enter 3.'
                  '\n   Use MM averages to determine outliers and fill in missing data, enter 4 (Recommended).'
                  )
            choice = int(input("Enter your selection: "))
            loop = 1

            while loop:
                if 1 <= choice <= 4:
                    loop = 0
                else:
                    print('Please enter a valid option.')
                    choice = int(input('Specify which variable you would like to correct: '))

            corr_log.write('Selected temperature correction method for this interval was %s. \n' % choice)
            if choice == 1:
                mod = float(input("\nEnter the additive modifier you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] + mod
                corr_var2[int_start:int_end] = var2[int_start:int_end] + mod
                corr_log.write('Additive modifier applied for this interval was %s. \n' % mod)

            elif choice == 2:
                mod = float(input("\nEnter the multiplicative modifier (ex: 2 for x2) you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] * mod
                corr_var2[int_start:int_end] = var2[int_start:int_end] * mod
                corr_log.write('Multiplicative modifier applied for this interval was %s. \n' % mod)
            elif choice == 3:
                corr_var1[int_start:int_end] = numpy.nan
                corr_var2[int_start:int_end] = numpy.nan
                corr_log.write('Interval was set to NaN. \n')
            else:
                # Conduct first pass
                points_removed = numpy.zeros((2, 2))
                limit = float(input('\nSpecify the maximum departure from '
                                    'monthly mean (in degrees C) to determine outliers: '))
                # Create average monthly temperatures
                mon_var1 = []
                mon_var2 = []
                var1_std = []
                var2_std = []
                k = 1
                while k <= 12:
                    t_index = [ex for ex, ind in enumerate(mon) if ind == k]
                    t_index = numpy.array(t_index)

                    mon_var1.append(numpy.nanmean(var1[t_index]))
                    var1_std.append(numpy.nanstd(var1[t_index]))

                    mon_var2.append(numpy.nanmean(var2[t_index]))
                    var2_std.append(numpy.nanstd(var2[t_index]))
                    k += 1
                # Conduct first pass to throw out outliers
                i = int_start
                while i < int_end:
                    if (var1[i] > mon_var1[mon[i] - 1] + limit) or (var1[i] < mon_var1[mon[i] - 1] - limit):
                        # Outside of cutoff
                        corr_var1[i] = mon_var1[mon[i] - 1] + (var1_std[mon[i] - 1] * random.uniform(-1, 1))
                        points_removed[0, 0] += 1
                    else:
                        # Inside of cutoff
                        pass
                    if (var2[i] > mon_var2[mon[i] - 1] + limit) or (var2[i] < mon_var2[mon[i] - 1] - limit):
                        # Outside of cutoff
                        corr_var2[i] = mon_var2[mon[i] - 1] + (var2_std[mon[i] - 1] * random.uniform(-1, 1))
                        points_removed[0, 1] += 1
                    else:
                        # Inside of cutoff
                        pass
                    i += 1
                print(str(points_removed[0, 0]) + ' points removed by first pass on variable 1.')
                print(str(points_removed[0, 1]) + ' points removed by first pass on variable 2.')

                corr_log.write('First pass temperature limit was %s degrees, var 1 removed %s, var 2 removed %s. \n'
                               % (limit, str(points_removed[0, 0]), str(points_removed[0, 1])))

                # Conduct second pass
                limit = float(input('\nSpecify the maximum departure from '
                                    'monthly mean (in degrees C) to determine outliers: '))
                # Create average monthly temperatures
                mon_var1 = []
                mon_var2 = []
                var1_std = []
                var2_std = []
                k = 1
                while k <= 12:
                    t_index = [ex for ex, ind in enumerate(mon) if ind == k]
                    t_index = numpy.array(t_index)

                    mon_var1.append(numpy.nanmean(corr_var1[t_index]))
                    var1_std.append(numpy.nanstd(corr_var1[t_index]))

                    mon_var2.append(numpy.nanmean(corr_var2[t_index]))
                    var2_std.append(numpy.nanstd(corr_var2[t_index]))
                    k += 1
                # Conduct first pass to throw out outliers
                i = int_start
                while i < int_end:

                    if (corr_var1[i] > mon_var1[mon[i] - 1] + limit) or (corr_var1[i] < mon_var1[mon[i] - 1] - limit):
                        # Outside of cutoff
                        corr_var1[i] = mon_var1[mon[i] - 1] + (var1_std[mon[i] - 1] * random.uniform(-1, 1))
                        points_removed[1, 0] += 1
                    else:
                        # Inside of cutoff
                        pass
                    if (corr_var2[i] > mon_var2[mon[i] - 1] + limit) or (corr_var2[i] < mon_var2[mon[i] - 1] - limit):
                        # Outside of cutoff
                        corr_var2[i] = mon_var2[mon[i] - 1] + (var2_std[mon[i] - 1] * random.uniform(-1, 1))
                        points_removed[1, 1] += 1
                    else:
                        # Inside of cutoff
                        pass

                    i += 1
                print(str(points_removed[1, 0]) + ' points removed by second pass on variable 1.')
                print(str(points_removed[1, 1]) + ' points removed by second pass on variable 2.')
                corr_log.write('Second pass temperature limit was %s degrees, var 1 removed %s, var 2 removed %s. \n'
                               % (limit, str(points_removed[1, 0]), str(points_removed[1, 1])))

                # RH data
        elif code == 2:
            print('\nPlease select the method to use to correct this Relative Humidity data:'
                  '\n   For user-defined additive value correction, enter 1.'
                  '\n   For user-defined multiplicative value correction, enter 2.'
                  '\n   To set everything in this interval to NaN, enter 3.'
                  '\n   To correct based on yearly percentiles, enter 4 (Recommended).'
                  )
            choice = int(input("Enter your selection: "))
            loop = 1

            while loop:
                if 1 <= choice <= 4:
                    loop = 0
                else:
                    print('Please enter a valid option.')
                    choice = int(input('Specify which variable you would like to correct: '))

            corr_log.write('Selected humidity correction method for this interval was %s. \n' % choice)
            if choice == 1:
                mod = float(input("\nEnter the additive modifier you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] + mod
                corr_var2[int_start:int_end] = var2[int_start:int_end] + mod
                corr_log.write('Additive modifier applied for this interval was %s. \n' % mod)

            elif choice == 2:
                mod = float(input("\nEnter the multiplicative modifier (ex: 2 for x2) you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] * mod
                corr_var2[int_start:int_end] = var2[int_start:int_end] * mod
                corr_log.write('Multiplicative modifier applied for this interval was %s. \n' % mod)

            elif choice == 3:
                corr_var1[int_start:int_end] = numpy.nan
                corr_var2[int_start:int_end] = numpy.nan
                corr_log.write('Interval was set to NaN. \n')

            else:
                # Corrects the data based on a year-based percentile correction
                corr_thresh = float(input("\nEnter the percentile threshold to use for this correction (rec. 90): "))

                # ID unique years in data set
                unique_years = numpy.unique(yr)
                percentile_yr = numpy.zeros(unique_years.size)
                rh_corr_per_yr = numpy.zeros(unique_years.size)

                # The following code was sourced from Shey back in ~2008
                for j in range(unique_years.size):
                    count = 0
                    rh_yr = []

                    # This loop goes through and isolates all RH values that fall within each year to calculate
                    # the correction percentile for that year
                    for k in range(var_size):
                        if unique_years[j] == yr[k]:
                            rh_yr.append(var1[k])
                            count += 1  # counts the number of days in the year

                    percentile_yr[j] = numpy.nanpercentile(rh_yr, corr_thresh)
                    rh_corr_per_yr[j] = 100 / percentile_yr[j]
                    print("\n" + str(count) + " Days were included in year " + str(j) + " of the RH correction process.")

                # Check to see if the years are lined up, I.E. data file starts in 2001 but correction starts in 2004
                count = 0
                if int_start != 0:
                    align_bool = 1
                    while align_bool == 1:
                        if yr[int_start] != unique_years[count]:
                            count += 1
                        else:
                            align_bool = 0
                else:
                    pass

                # Now we apply the correction to both RHmax and RHmin
                # Taking care to keep the data year lined up with the correction value we are using
                rhmax_cutoff = 0
                rhmin_cutoff = 0
                for i in range(int_start,int_end):
                    if unique_years[count] == yr[i]:
                        corr_var1[i] = var1[i] * rh_corr_per_yr[count]
                        corr_var2[i] = var2[i] * rh_corr_per_yr[count]
                    else:
                        # Encountered last day of year, increment to next correction year and continue
                        count += 1
                        corr_var1[i] = var1[i] * rh_corr_per_yr[count]
                        corr_var2[i] = var2[i] * rh_corr_per_yr[count]

                    # Check for corrected values exceeding 100%
                    if corr_var1[i] > 100:
                        corr_var1[i] = 100
                        rhmax_cutoff += 1
                    elif corr_var1[i] < 0:
                        corr_var1[i] = 0
                    else:
                        pass

                    if corr_var2[i] > 100:
                        corr_var2[i] = 100
                        rhmin_cutoff += 1
                    elif corr_var2[i] < 0:
                        corr_var2[i] = 0
                    else:
                        pass

                print("\n" + str(rhmax_cutoff) + " RHMax data points were removed for exceeding the logical limit of 100%.")
                print("\n" + str(rhmin_cutoff) + " RHMin data points were removed for exceeding the logical limit of 100%.")

                corr_log.write('Year-based RH correction used the %s th percentile, RHMax had %s points exceed 100,'
                               ' RHMin had %s points exceed 100. \n'
                               % (corr_thresh, rhmax_cutoff, rhmin_cutoff))
        # Solar data
        elif code == 3:
            print('\nPlease select the method to use to correct this solar radiation data:'
                  '\n   For user-defined additive value correction, enter 1.'
                  '\n   For user-defined multiplicative value correction, enter 2.'
                  '\n   To set everything in this interval to NaN, enter 3.'
                  '\n   To correct based on periodic percentile intervals, enter 4 (Recommended).'
                  )
            choice = int(input("Enter your selection: "))
            loop = 1

            while loop:
                if 1 <= choice <= 4:
                    loop = 0
                else:
                    print('Please enter a valid option.')
                    choice = int(input('Specify which variable you would like to correct: '))
            corr_log.write('Selected solar radiation correction method for this interval was %s. \n' % choice)
            if choice == 1:
                mod = float(input("\nEnter the additive modifier you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] + mod
                corr_log.write('Additive modifier applied for this interval was %s. \n' % mod)
            elif choice == 2:
                mod = float(input("\nEnter the multiplicative modifier (ex: 2 for x2) you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] * mod
                corr_log.write('Multiplicative  modifier applied for this interval was %s. \n' % mod)
            elif choice == 3:
                corr_var1[int_start:int_end] = numpy.nan
                corr_log.write('Interval was set to NaN. \n')
            else:
                discard_thresh = float(input('\nEnter the discard threshold as a percentage integer (recommended 99): '))
                corr_period = int(input('\nEnter the number of days each correction period will last (rec. 60): '))
                corr_thresh = float(input('\nEnter the correction threshold as a percentage integer (recommended 90): '))

                # begin by despiking rs data, all values removed are set to NaN
                despike_ratios = var1 / var2
                despike_discard = numpy.nanpercentile(despike_ratios, discard_thresh)

                despike_counter = 0
                i = int_start
                while i < int_end:
                    if despike_ratios[i] > despike_discard:
                        var1[i] = numpy.nan
                        despike_counter += 1
                    else:
                        pass
                    i += 1
                print("\n" + str(despike_counter) + " points were removed as part of the despiking procedure.")

                corr_log.write('Periodic Percentile Rs corrections were applied, despiking percentile was %s,'
                               ' period length was %s, and correction percentile was %s. \n'
                               % (discard_thresh, corr_period, corr_thresh))
                corr_log.write('%s data points were removed as part of the despiking process. \n'
                               % despike_counter)

                # now that data is despiked, correction can begin, pass to function to determine values for each period
                corr_values_var1 = rs_percent_corr(int_start, int_end, var1, var2, corr_thresh, corr_period)

                # now apply those values to the data for each period
                x = int_start  # index that tracks along data points for full interval
                y = 0  # index that tracks how far along a period we are
                z = 0  # index that tracks which correction period we are in
                while x < len(var1) and x < int_end and z < len(corr_values_var1):
                    # i is less than the length of var1 to prevent OOB,
                    # and is before or at the end of the correction interval
                    # and we have not yet run out of correction periods
                    if y <= corr_period:
                        # if y is less than the size of a correction period
                        corr_var1[x] = var1[x] / corr_values_var1[z]
                        # Clip rs if it goes past rso
                        if corr_var1[x] > var2[x]:
                            corr_var1[x] = var2[x]
                        else:
                            pass

                        x += 1
                        y += 1

                    else:
                        # We have reached the end of the correction period, go to next period
                        y = 1
                        z += 1

        # Wind or Precipitation or Vapor Pressure
        else:
            print('\nPlease select the method to use to correct this wind or precipitation data:'
                  '\n   For user-defined additive value correction, enter 1.'
                  '\n   For user-defined multiplicative value correction, enter 2.'
                  '\n   To set everything in this interval to NaN, enter 3.'
                  )
            choice = int(input("Enter your selection: "))
            loop = 1

            while loop:
                if 1 <= choice <= 3:
                    loop = 0
                else:
                    print('Please enter a valid option.')
                    choice = int(input('Specify which variable you would like to correct: '))

            corr_log.write('Selected correction method for this interval was %s. \n' % choice)
            if choice == 1:
                mod = float(input("\nEnter the additive modifier you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] + mod
                corr_log.write('Additive modifier applied for this interval was %s. \n' % mod)
            elif choice == 2:
                mod = float(input("\nEnter the multiplicative modifier (ex: 2 for x2) you want to apply to all values: "))
                corr_var1[int_start:int_end] = var1[int_start:int_end] * mod
                corr_log.write('Multiplicative modifier applied for this interval was %s. \n' % mod)
            elif choice == 3:
                corr_var1[int_start:int_end] = numpy.nan
                corr_log.write('Interval was set to NaN. \n')

        # ############################################################################################
        # Set up plot, will have three components, section 1 will be raw data, section 2 will be corrected data
        # section three will be delta change, and section 4 will be % difference

        reset_output()  # clears bokeh output, prevents ballooning file sizes
        output_file(station + "_" + title_string + "_correction_graph.html")
        cs1 = figure(
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' Original',
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        cs1.line(dates, backup_var1, line_color="black", legend="Original " + var1n)
        if var2_flag == 1:
            cs1.line(dates, backup_var2, line_color="blue", legend="Original " + var2n)
        else:
            pass
        cs1.legend.location = "bottom_left"

        cs2 = figure(
            x_range=cs1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' Corrected',
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        cs2.line(dates, corr_var1, line_color="black", legend="Corrected " + var1n)
        if var2_flag == 1:
            cs2.line(dates, corr_var2, line_color="blue", legend="Corrected " + var2n)
        else:
            pass
        cs2.legend.location = "bottom_left"

        cs3 = figure(
            x_range=cs1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' Deltas',
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        cs3.line(dates, corr_var1 - backup_var1, line_color="black", legend="Delta of " + var1n)
        if var2_flag == 1:
            cs3.line(dates, corr_var2 - backup_var2, line_color="blue", legend="Delta of " + var2n)
        else:
            pass
        cs3.legend.location = "bottom_left"

        cs4 = figure(
            x_range=cs1.x_range,
            width=x_size, height=y_size, x_axis_type="datetime",
            x_axis_label='Timestep', y_axis_label='Values', title=title_string + ' % Difference',
            tools='pan, box_zoom, undo, reset, hover, save'
        )
        cs4.line(dates, ((corr_var1 - backup_var1)/backup_var1)*100, line_color="black",
                 legend="% Difference of " + var1n)
        if var2_flag == 1:
            cs4.line(dates, ((corr_var2 - backup_var2)/backup_var2)*100, line_color="blue",
                     legend="% Difference of " + var2n)
        else:
            pass
        cs4.legend.location = "bottom_left"

        corrfig = gridplot([[cs1], [cs2], [cs3], [cs4]], toolbar_location="left")
        show(corrfig)

        ###############################################################################################################
        # Correction has been performed and results displayed, now ask user for repeat/discard/keep changes
        print('\nAre you done correcting?'
              '\n   Enter 1 for yes.'
              '\n   Enter 2 for another iteration.'
              '\n   Enter 3 to start over.'
              '\n   Enter 4 to discard all changes.'
              )

        choice = int(input("Enter your selection: "))
        loop = 1
        while loop:
            if 1 <= choice <= 4:
                loop = 0
            else:
                print('Please enter a valid option.')
                choice = int(input('Enter your selection: '))

        if choice == 1:
            redo_loop = 0
            corr_log.write('---->Correction is now complete. \n\n')
        elif choice == 2:
            var1 = numpy.array(corr_var1)
            var2 = numpy.array(corr_var2)
            corr_log.write('---->The variables are being subject to another round of correction. \n\n')
        elif choice == 3:
            var1 = numpy.array(backup_var1)
            var2 = numpy.array(backup_var2)
            corr_var1 = numpy.array(backup_var1)
            corr_var2 = numpy.array(backup_var2)
            corr_log.write('--->User has elected to throw out all rounds of correction and start again. \n\n')
        else:
            redo_loop = 0
            corr_var1 = numpy.array(backup_var1)
            corr_var2 = numpy.array(backup_var2)
            corr_log.write('--->User has elected to throw out all rounds of correction and exit to the main script.'
                           ' \n\n')

    # return corrected variables, or originals if correction was rejected
    corr_log.close()
    return corr_var1, corr_var2


# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
