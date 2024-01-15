########################
QC Procedure Information
########################

This page contains details on the correction methods used by agweather-qaqc. The methods chosen could be summed up as:

**Make as few changes as possible to fix bad trends in data without sacrificing the real measured qualities of said data.**

Limits on Data
==============
The following limits are used when reading in the data to determine any unreasonable values, which are then removed.

* -50 C <= Temperature <= 60 C
* 0 m/s < Wind Speed <= 35 m/s
* 0 mm <= Precipitation <= 610 mm
* 5 w/m2 <= Solar Radiation <= 700 w/m2
* 0 kPa <= Vapor Pressure <= 8 kPa  #
* 2% < Relative Humidity < 110%

The number of points from each variable removed by these limits are saved in the log file.


Suggested Correction Order
==========================
Because some variables are reliant on others (Ex. correction solar radiation is dependent on clear-sky solar radiation
which is dependent on humidity) there is a suggested order to the QC process:

1. Temperature Maximum and Minimum
2. Windspeed
3. Precipitation
4. Any Humidity Variables
5. Solar Radiation

Suggested Correction Parameters
===============================
When using this package, you will be asked for what correction parameters you want, which will
change how the correction factors are calculated and applied. In the process of developing this software,
certain parameters were found to provide good results. Those parameters are listed here, and appear in the
documentation below. **You are not restricted to using these parameters, but they will change the resulting final data.**

We suggest the following parameters when using this software:

**Relative Humidity**
We recommend using the top 1% of data points in each year to calculate the correction ratio. Information about
the climate of the station may allow you to go higher, but if it is an arid station you should pick a small number to
avoid simulating days with rainfall that may not have occurred.

**Solar Radiation**
We recommend dividing the record into 60-day periods and then using the largest 6 solar radiation/clear-sky solar ratios
to calculate the correction ratio. The period should be sufficiently large enough to allow for a good sampling period,
but it shouldn't be so long as to sampling across winter/summer seasons.  The number of datapoints should be large
enough to get an accurate sampling of variations within the period but it should not be so large as to force
a correction that would force cloudy days to represent clear days.


Temperature Correction
======================
Temperature correction is done by removing outliers using a modified z-score approach based on median absolute deviation as described in:

Boris Iglewicz and David Hoaglin (1993) Volume 16: How to Detect and Handle Outliers, The ASQC Basic References in Quality Control: Statistical Techniques

The process occurs in the following steps:

1. Temperature values are divided into subgroups based on what month they occur in.
2. Each group (twelve total groups) of temperature values has its median absolute deviation calculated.
3. That median absolute deviation is used to calculate a z-score for every temperature value within the group.
4. Any value that exceeds the z-score threshold of 3.5 is removed as a likely outlier. The threshold of 3.5 is recommended by Iglewicz and Hoaglin.
5. The data, once free of outliers, is considered corrected.

Generally, temperature data suffers from discrete outliers introduced from equipment malfunctions rather than chronic problems like sensor drift.
Checking for outliers with an outlier-resistant method such as this allows for the removal of those outliers without modifying the rest of
the data.

Wind and Precipitation
======================

There are no easy, reliable ways for us to infer what reasonable wind or precipitation data should be when presented with bad values,
such as suspiciously high amounts of rainfall or wind data that remains constant over time. For these variables it is recommended to
just throw remove bad or suspect values.

Relative Humidity Max/Min Correction
====================================
Relative humidity correction is done through a year-based percentile approach, broken down into these steps:

1. Divide the entire record into periods based on calendar years (365-366 values per year).
2. Remove all nans from within each calendar year.
3. Find the top 1% RHMax values within each calendar year once NaNs have been removed by dividing the number of non-nan
   days by 100, rounding down, but with a minimum of one, and finding that many largest values (3 for a full year). This
   division of the year by 100 is to prevent years at the start and end of record that may not have a full year from being oversampled.
4. Take the average of those values.
5. Calculate the ratio of 100 and that RHMax average.
6. Multiply every RHMax value within each calendar year with its corresponding 100/RHMax average.
7. Multiply every RHMin value within each calendar year with its corresponding 100/RHMax average.
8. If any points of RHMax or RHMin are greater than 100% post correction, those points are set to equal 100. If any
   points of RHMax or RHMin are less than 0% post correction,  those points are set equal to 0.
   If RHMax is less than RHMin ( as an error in initial dataset), that RHMax and Min are thrown out.
9. The data is now considered corrected.

One of the most common problems with RH data is sensor drift that occurs slowly over time. This pattern is visible
in the test_data.csv dataset that is provided in the repository. A year-based percentile approach allows for
steadily-increasing correction factors over time to fix this, and making the periods of correction years will ideally
make each period have all four seasons, which is important in arid locations or other places with seasonal rainfall.

.. caution::
   This method assumes daily RH values that have been calculated from subdaily RH values. If RH is computed from
   measured dewpoint temperature then this method is not reliable. However, if dewpoint temperature is provided
   and directly measured, using dewpoint data is preferable to using relative humidity data.

Vapor Pressure and RH Average
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As with wind and precipitation data, there are no easy, reliable ways for us to infer what vapor pressure or average relative humidity should
be when presented with bad values, for these variables it is recommended to just throw remove bad or suspect values, or instead choose
to use a variable like RH Max/Min and Dewpoint Temperature than you can QC.

Solar Radiation Correction
==========================
Correcting solar radiation data is done through a period-based percentile correction, which occurs in the following steps:

1. The user-selected interval of both Rs and Rso new sections being divided into user-defined periods.
2. Each period then has a correction factor calculated based on the user-specified largest number of points for rs/rso. Averages are formed for both rs and rso of those largest points, and then this average rso is divided by this average rs to get a final ratio, which will be multiplied to all points within its corresponding period.
3. Within each period, the code checks for the existence of potential isolated erroneous readings (electrical shorts, datalogger errors, etc.). The logic for how this works can be found in the `function documentation <agweatherqaqc.html#agweatherqaqc.qaqc_functions.rs_period_ratio_corr>`_.
4. If a period does not contain enough valid data points to fill the user-specified number, the entire period is thrown out. To prevent the code from correcting data beyond the point of believability, if the correction factor is below 0.5 or above 1.5, the data for that period is removed instead.
5. In addition, if the correction factor is between 0.97 < X < 1.03, the data is unchanged under the assumption that the sensor was behaving as expected.
6. The function returns the corrected solar radiation that has had erroneous readings removed (if applicable) and the period-based correction factor applied. Post-correction Rs data that exceeds Rso by 3% is clipped to Rso.

**Rs correction is dependant on Rso values, which itself is dependant on humidity data. We recommend Rs is corrected last
so that we can use the best-possible Rso for the correction process.**

Solar radiation is more likely to have problems than other weather data, and will frequently have bad values and sensor drift
occurring together. This period-based percentile approach that tracks the number of times measured solar radiation exceeds theoretical clear-sky
solar radiation allows for the correction of progressive sensor drift while at the same time catching voltage spikes during the period.
The limit of 3 observations in each 60-day period is to account for stations where Rs constantly exceeds Rso, either due to
poor calibration or some natural factor like additional reflected solar radiation from objects like clouds.
