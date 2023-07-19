import logging as log
import numpy as np
from refet import Daily
from refet.calcs import _ra_daily, _rso_daily


def calc_temperature_variables(month, tmax, tmin, tdew):
    """
        Calculates all of the following temperature variables:
            delta_t : the daily difference between maximum temperature and minimum temperature
            k_not : the daily difference between minimum temperature and dewpoint temperature
            monthly_tmin : monthly averaged minimum temperature (12 values total) values across all of record
            monthly_tdew : monthly averaged dewpoint temperature (12 values total) values across all of record
            monthly_delta_t : monthly averaged delta_t (12 values total) values across all of record
            monthly_k_not : monthly averaged k_not (12 values total) values across all of record

        Parameters:
            month : 1D numpy array of month values for use in mean monthly calculations
            tmax : 1D numpy array of maximum temperature values
            tmin : 1D numpy array of minimum temperature values
            tdew : 1D numpy array of dewpoint temperature values

        Returns:
            Returns all variables listed above as 1D numpy arrays
    """
    delta_t = np.array(tmax - tmin)
    k_not = np.array(tmin - tdew)  # ASCE Ref Appendix E Eq. 1
    monthly_tmin = np.empty(12)
    monthly_tdew = np.empty(12)
    monthly_delta_t = np.empty(12)
    monthly_k_not = np.empty(12)

    # Create average monthly delta_t and average monthly k_not for downstream analysis
    j = 1
    for k in range(12):
        temp_indexes = [ex for ex, ind in enumerate(month) if ind == j]
        temp_indexes = np.array(temp_indexes, dtype=int)

        monthly_tmin[k] = np.nanmean(tmin[temp_indexes])
        monthly_tdew[k] = np.nanmean(tdew[temp_indexes])
        monthly_delta_t[k] = np.nanmean(delta_t[temp_indexes])
        monthly_k_not[k] = np.nanmean(k_not[temp_indexes])

        j += 1

    return delta_t, monthly_delta_t, k_not, monthly_k_not, monthly_tmin, monthly_tdew


def calc_humidity_variables(tmax, tmin, tavg, ea, ea_col, tdew, tdew_col, rhmax, rhmax_col, rhmin, rhmin_col,
                            rhavg, rhavg_col):
    """
        Takes in all possible humidity variables and figures out which one to use for the calculation of TDew and Ea.
        Unless otherwise cited, all equations are from ASCE refet manual
        Which variables used is determined by the variable column values in the input file, but will follow this path:
            If Ea exists but Tdew doesn't exist, use Ea to calculate Tdew.
            If Ea doesn't exist but Tdew does, use Tdew to calculate Ea.
            If neither exist but RHmax and RHmin exist, use those to calculate both Ea and Tdew.
            If nothing else exists, use RHAvg to calculate both Ea and Tdew.
            If both Ea and TDew exist, then the function just returns those values.

        Parameters:
            tmax : 1D array of maximum temperature values
            tmin : 1D array of minimum temperature values
            tavg : 1D array of average temperature values
            ea : 1D array of vapor pressure values, which may be empty
            ea_col : column of ea variable in data file, if it was provided
            tdew : 1D array of dewpoint temperature values, which may be empty
            tdew_col : column of tdew variable in data file, if it was provided
            rhmax : 1D array of maximum relative humidity values, which may be empty
            rhmax_col : column of rhmax variable in data file, if it was provided
            rhmin : 1D array of minimum relative humidity values, which may be empty
            rhmin_col : column of rhmin variable in data file, if it was provided
            rhavg : 1D array of average relative humidity values, which may be empty
            rhavg_col : column of rhavg variable in data file, if it was provided

        Returns:
            Returns both Ea and TDew as numpy arrays
    """

    # Check to see if TDew exists, if it does not, then check to see what else exists so it can be calculated.
    if tdew_col == -1:  # We are not given TDew

        if ea_col != -1:  # Vapor Pressure exists, so it will be used to calculate TDew

            calc_ea = np.array(ea)
            # Calculate TDew using actual vapor pressure
            # Below equation was taken from the book "Evapotranspiration: Principles and
            # Applications for Water Management" by Goyal and Harmsen, Eq. 9 in chapter 13, page 320.
            calc_tdew = np.array((116.91 + (237.3 * np.log(calc_ea))) / (16.78 - np.log(calc_ea)))

            return calc_ea, calc_tdew

        elif ea_col == -1 and rhmax_col != -1 and rhmin_col != -1:  # RHmax and RHmin exist but Ea does not exist

            eo_tmax = np.array(0.6108 * np.exp((17.27 * tmax) / (tmax + 237.3)))  # units kPa, EQ 7
            eo_tmin = np.array(0.6108 * np.exp((17.27 * tmin) / (tmin + 237.3)))  # units kPa, EQ 7

            calc_ea = np.array(((eo_tmin * (rhmax / 100)) + (eo_tmax * (rhmin / 100))) / 2)  # EQ 11
            calc_tdew = np.array((116.91 + (237.3 * np.log(calc_ea))) / (16.78 - np.log(calc_ea)))  # EQ cited above

            return calc_ea, calc_tdew

        elif ea_col == -1 and rhmax_col == -1 and rhmin_col == -1 and rhavg_col != -1:  # Only RHAvg exists, so use it

            eo_tavg = np.array(0.6108 * np.exp((17.27 * tavg) / (tavg + 237.3)))  # units kPa, EQ 7
            calc_ea = np.array(eo_tavg * (rhavg / 100))  # EQ 14
            calc_tdew = np.array((116.91 + (237.3 * np.log(calc_ea))) / (16.78 - np.log(calc_ea)))  # EQ cited above

            return calc_ea, calc_tdew

        else:
            # If an unsupported combination of humidity variables is passed, raise a value error.
            raise ValueError('calc_humidity_variables encountered an unexpected combination of inputs.')

    elif tdew_col != -1:
        # We are given tdew, so we check to see if ea also exists.
        calc_tdew = np.array(tdew)

        if ea_col == -1:  # Vapor pressure not given, have to calculate from tdew
            calc_ea = np.array(0.6108 * np.exp((17.27 * calc_tdew) / (calc_tdew + 237.3)))  # EQ 8, units kPa
        elif ea_col != -1:
            # Vapor pressure and tdew were both provided so we don't need to calculate either.
            calc_ea = np.array(ea)
        else:
            # If an unsupported combination of humidity variables is passed, raise a value error.
            raise ValueError('calc_humidity_variables encountered an unexpected combination of inputs.')

        return calc_ea, calc_tdew

    else:
        # If an unsupported combination of humidity variables is passed, raise a value error.
        raise ValueError('calc_humidity_variables encountered an unexpected combination of inputs.')


def calc_rso_and_refet(lat, elev, wind_anemom, doy, month, tmax, tmin, ea, uz, rs):
    """
        Calculates all of the following variables using the refet package (https://github.com/DRI-WSWUP/RefET):
            rso : clear sky solar radiation
            monthly_rs : : monthly averaged solar radiation (12 values total) values across all of record
            eto : grass reference evapotranspiration in units mm/day
            etr : alfalfa reference evapotranspiration in units mm/day
            monthly_eto : monthly averaged grass reference ET (12 values total) values across all of record
            monthly_etr : monthly averaged alfalfa reference ET (12 values total) values across all of record

        Parameters:
            lat : station latitude in decimal degrees
            elev: station elevation in meters
            wind_anemom : height of windspeed anemometer in meters
            doy : 1D numpy array of day of year in record
            month : 1D numpy array of current month in record
            tmax : 1D numpy array of maximum temperature values
            tmin : 1D numpy array of minimum temperature values
            ea : 1D numpy array of vapor pressure in kPa
            uz : 1D numpy array of average windspeed values
            rs : 1D numpy array of solar radiation values

        Returns:
            Returns all variables listed above as 1D numpy arrays
    """

    data_size = month.shape[0]  # Size of data set
    ra = np.empty(data_size)  # Extraterrestrial solar radiation, MJ/m2, ASCE eq. 21
    rso = np.empty(data_size)  # Clear sky solar radiation, MJ/m2, ASCE eq. 16
    eto = np.empty(data_size)
    etr = np.empty(data_size)
    monthly_rs = np.empty(12)
    monthly_eto = np.empty(12)
    monthly_etr = np.empty(12)

    pressure = 101.3 * (((293 - (0.0065 * elev)) / 293) ** 5.26)  # units kPa, EQ 3 in ASCE RefET manual
    # refet package expects rs in MJ/m2 and latitude in radians
    refet_input_rs = np.array(rs * 0.0864)  # convert W/m2 to  MJ/m2
    refet_input_lat = lat * (np.pi / 180.0)  # convert latitude into radians

    # Calculate daily values
    for i in range(data_size):
        ra[i] = _ra_daily(lat=refet_input_lat, doy=doy[i], method='asce')
        rso[i] = _rso_daily(ra=ra[i], ea=ea[i], pair=pressure, doy=doy[i], lat=refet_input_lat)

        # Calculating ETo in mm using refET package
        eto[i] = Daily(tmin=tmin[i], tmax=tmax[i], ea=ea[i], rs=refet_input_rs[i], uz=uz[i], zw=wind_anemom,
                       elev=elev, lat=lat, doy=doy[i], method='asce').eto()

        # Calculating ETr in mm using refET package
        etr[i] = Daily(tmin=tmin[i], tmax=tmax[i], ea=ea[i], rs=refet_input_rs[i], uz=uz[i], zw=wind_anemom,
                       elev=elev, lat=lat, doy=doy[i], method='asce').etr()

    # Calculate mean monthly values
    j = 1
    for k in range(12):
        temp_indexes = [ex for ex, ind in enumerate(month) if ind == j]
        temp_indexes = np.array(temp_indexes, dtype=int)

        monthly_rs[k] = np.nanmean(rs[temp_indexes])
        monthly_eto[k] = np.nanmean(eto[temp_indexes])
        monthly_etr[k] = np.nanmean(etr[temp_indexes])

        j += 1

    rso *= 11.574  # Convert rso from MJ/m2 to w/m2
    return rso, monthly_rs, eto, etr, monthly_eto, monthly_etr


def calc_rs_tr(month, rso, delta_t, mm_delta_t, b_zero, b_one, b_two):
    """
        Calculates theoretical daily solar radiation according to the Thornton and Running 1999 model.
        Paper can be found here: http://www.engr.scu.edu/~emaurer/chile/vic_taller/papers/thornton_running_1997.pdf
        Brief summary: Estimates rs based on a b coeff that is unique per each month based on temperature history
            and daily difference between maximum and minimum temperature and rso

        Parameters:
            month : 1D numpy array of months within dataset
            rso : 1D numpy array of clear-sky solar radiation values in w/m2
            delta_t : 1D numpy array of difference between maximum and minimum temperature values for the time step
            mm_delta_t : monthly averaged delta_t (12 values total) values across all of record
            b_zero : first B coefficient used in calculation of rs_tr, original value is 0.031
            b_one : second B coefficient used in calculation of rs_tr, original value is 0.201
            b_two :third B coefficient used in the calculation of rs_tr, original value is -0.185

        Returns:
            rs_tr : 1D numpy array of thornton-running solar radiation
            mm_rs_tr : monthly averaged rs_tr (12 values total) values across all of record
    """
    mm_rs_tr = np.empty(12)
    b_coefficient = np.array(b_zero + b_one * np.exp(b_two * mm_delta_t))
    rs_tr = np.array(rso * (1 - 0.9 * np.exp(-1 * b_coefficient[month - 1] * delta_t ** 1.5)))

    # Create mean monthly values
    j = 1
    for k in range(12):
        temp_indexes = [ex for ex, ind in enumerate(month) if ind == j]
        temp_indexes = np.array(temp_indexes, dtype=int)

        mm_rs_tr[k] = np.nanmean(rs_tr[temp_indexes])
        j += 1

    return rs_tr, mm_rs_tr


def calc_org_and_opt_rs_tr(mc_iterations, log_path, month, delta_t, mm_delta_t, rs, rso):
    """
        This function performs a monte carlo simulation on the b coefficients that go into generating thornton-
        running solar radiation in an attempt to optimize a model that best fits observed solar radiation data.
        That best fit model will then be used to fill any missing observations in actual solar radiation for the
        calculation of reference evapotranspiration. See the function calc_rs_tr for more information.

        The number of iterations is currently set to 1000, and the bracket size with which to generate random values
        is 0.5, these factors were chosen after trying different values on several stations and were a good balance of
        minimizing RMSE and processing speed.

        When running the script on the first mode, only 50 iterations are done to save time, it may be that optimized
        has worse parameters than original in this case, so we just return the original paramaters as the optimized

        Parameters:
            mc_iterations : number of iterations in monte carlo simulation
            log_path : path to log file that we will write the b coefficients and other relevant info to
            month : 1D numpy array of months within dataset
            rs : 1D numpy array of observed solar radiation values in w/m2
            rso : 1D numpy array of clear-sky solar radiation values in w/m2
            delta_t : 1D numpy array of difference between maximum and minimum temperature values for the time step
            mm_delta_t : monthly averaged delta_t (12 values total) values across all of record

        Returns:
            org_rs_tr : 1D numpy array of thornton-running solar radiation with original B coefficient values
            mm_org_rs_tr : monthly averaged org_rs_tr (12 values total) values across all of record
            opt_rs_tr : 1D numpy array of thornton-running solar radiation with optimized B coefficient values
            mm_opt_rs_tr : monthly averaged opt_rs_tr (12 values total) values across all of record
    """
    print("\nSystem: Now performing a Monte Carlo simulation to optimize Thornton Running solar radiation parameters.")
    print("\nSystem: %s iterations are being run, this may take some time." % mc_iterations)

    b_zero = np.array(0.031 + (0.031 * 0.5) * np.random.uniform(low=-1, high=1, size=mc_iterations))
    b_one = np.array(0.201 + (0.201 * 0.5) * np.random.uniform(low=-1, high=1, size=mc_iterations))
    b_two = np.array(-0.185 + (-0.185 * 0.5) * np.random.uniform(low=-1, high=1, size=mc_iterations))

    mc_rmse = np.zeros(mc_iterations)

    # Calculate rs_tr using original, unoptimized B coefficients
    (orig_rs_tr, mm_orig_rs_tr) = calc_rs_tr(month, rso, delta_t, mm_delta_t, 0.031, 0.201, -0.185)

    for i in range(mc_iterations):
        # Run all randomized b coefficients through thornton running calculation
        (mc_rs_tr, mm_mc_rs_tr) = calc_rs_tr(month, rso, delta_t, mm_delta_t, b_zero[i], b_one[i], b_two[i])

        mc_rmse[i] = np.sqrt(np.nanmean((mc_rs_tr - rs) ** 2))  # Calculate RMSE to track how good those parameters were

        if (i % 100) == 0:  # Update user so they don't think script is frozen.
            print('\nSystem: processing Thornton-Running iteration: {}'.format(i))
        else:
            pass

    # Now that we've iterated through all variations, find the best one
    min_rmse_index = np.nanargmin(mc_rmse)
    # Calculate RMSE of original rs_tr B coefficients
    orig_rmse = np.sqrt(np.nanmean((orig_rs_tr - rs) ** 2))

    print('\nSystem: original coefficients for TR Solar Radiation produced an RMSE of: {0:.4f}'.format(orig_rmse))
    print('System: optimized coefficients for TR Solar Radiation produced an RMSE of: {0:.4f}'.
          format(mc_rmse[min_rmse_index]))

    # Calculate the optimized rs_tr using the B coefficients that caused the lowest rmse
    (opt_rs_tr, mm_opt_rs_tr) = calc_rs_tr(month, rso, delta_t, mm_delta_t, b_zero[min_rmse_index],
                                           b_one[min_rmse_index], b_two[min_rmse_index])

    # Write the b coefficients used to the log file then close it
    log.basicConfig()
    corr_log = open(log_path, 'a')
    corr_log.write('\n\nThornton-Running Solar Radiation Optimization')
    corr_log.write('\nMonte Carlo simulation with %s iterations produced the coefficients:' % mc_iterations)
    corr_log.write('\nb_zero = {0:.4f}, b_one = {1:.4f}, b_two = {2:.4f}'.
                   format(b_zero[min_rmse_index], b_one[min_rmse_index], b_two[min_rmse_index]))
    corr_log.write('\nOptimized coefficients RMSE against observed solar radiation was: {0:.4f}'.
                   format(mc_rmse[min_rmse_index]))
    corr_log.write('\nOriginal coefficients RMSE against observed solar radiation was: {0:.4f} \n\n'
                   .format(orig_rmse))
    corr_log.close()

    if orig_rmse < mc_rmse[min_rmse_index] and mc_iterations == 50:
        # if original was better than optimized, it is likely because we didn't do enough iterations
        # which is likely because we're not correcting data, so just return original as optimized
        opt_rs_tr = orig_rs_tr
        mm_opt_rs_tr = mm_orig_rs_tr
    elif orig_rmse < mc_rmse[min_rmse_index] and mc_iterations != 50:
        # this shouldn't happen, as we should have done enough iterations to beat original values, so raise an error
        raise ValueError('Thornton running optimization failed to beat original coefficient values.' +
                         ' Try running again, and if this error persists please report it on github.')
    else:
        pass

    # Return both original and optimized rs_tr
    return orig_rs_tr, mm_orig_rs_tr, opt_rs_tr, mm_opt_rs_tr


def compile_ea(tmax, tmin, tavg, ea, tdew, tdew_col, rhmax, rhmax_col, rhmin, rhmin_col, rhavg, rhavg_col, tdew_ko):
    """
        This function is used to create a 'compiled' ea from all provided humidity variables, always using the best one
        provided within the dataset for each given day of the record. This function will work regardless of if ea is
        provided by the dataset or not.

        Parameters:
            tmax : 1D array of maximum temperature values
            tmin : 1D array of minimum temperature values
            tavg : 1D array of average temperature values
            ea : 1D array of vapor pressure values, which may be empty
            tdew : 1D array of dewpoint temperature values, which may be empty
            tdew_col : column of Tdew variable in data file, if it is provided
            rhmax : 1D array of maximum relative humidity values, which may be empty
            rhmax_col : column of rhmax variable in data file, if it was provided
            rhmin : 1D array of minimum relative humidity values, which may be empty
            rhmin_col : column of rhmin variable in data file, if it was provided
            rhavg : 1D array of average relative humidity values, which may be empty
            rhavg_col : column of rhavg variable in data file, if it was provided
            tdew_ko : 1D array of tdew data filled in by tmin-ko curve

        Returns:
            Returns a "complete" ea array
    """
    data_length = ea.shape[0]
    compiled_ea = np.empty(data_length) * np.nan
    tdew_calc_ea = np.empty(data_length) * np.nan
    rh_max_min_calc_ea = np.empty(data_length) * np.nan
    rh_avg_calc_ea = np.empty(data_length) * np.nan

    # TDew data filled in with TMin - Ko curve is always an option
    tdew_ko_calc_ea = np.array(0.6108 * np.exp((17.27 * tdew_ko) / (tdew_ko + 237.3)))  # EQ 8, units kPa

    if tdew_col != -1:  # Dewpoint temperature is provided

        tdew_calc_ea = np.array(0.6108 * np.exp((17.27 * tdew) / (tdew + 237.3)))  # EQ 8, units kPa

    if rhmax_col != -1 and rhmin_col != -1:  # relative humidity is provided

        eo_tmax = np.array(0.6108 * np.exp((17.27 * tmax) / (tmax + 237.3)))  # units kPa, EQ 7
        eo_tmin = np.array(0.6108 * np.exp((17.27 * tmin) / (tmin + 237.3)))  # units kPa, EQ 7

        rh_max_min_calc_ea = np.array(((eo_tmin * (rhmax / 100)) + (eo_tmax * (rhmin / 100))) / 2)  # EQ 11

    if rhavg_col != -1:  # RHAvg is provided

        eo_tavg = np.array(0.6108 * np.exp((17.27 * tavg) / (tavg + 237.3)))  # units kPa, EQ 7
        rh_avg_calc_ea = np.array(eo_tavg * (rhavg / 100))  # EQ 14

    for i in range(data_length):
        if np.isnan(ea[i]):  # Either Ea is provided or is already calculated by the best humidity variable available

            if not np.isnan(tdew_calc_ea[i]):
                compiled_ea[i] = tdew_calc_ea[i]

            elif np.isnan(tdew_calc_ea[i]) and not np.isnan(rh_max_min_calc_ea[i]):
                compiled_ea[i] = rh_max_min_calc_ea[i]

            elif np.isnan(tdew_calc_ea[i]) and np.isnan(rh_max_min_calc_ea[i]) and not np.isnan(rh_avg_calc_ea[i]):
                compiled_ea[i] = rh_avg_calc_ea[i]

            elif np.isnan(tdew_calc_ea[i]) and np.isnan(rh_max_min_calc_ea[i]) and np.isnan(rh_avg_calc_ea[i]):
                compiled_ea[i] = tdew_ko_calc_ea[i]

        else:  # ea exists here so no need to fill
            compiled_ea[i] = ea[i]

    return compiled_ea

# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
