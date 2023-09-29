import pandas as pd
import pytest as pt
import numpy as np
import math
from modules import input_functions, data_functions

metadata_file_path = 'test_files/test_metadata.xlsx'
config_file_path = 'test_files/test_config.ini'
data_file_path = 'test_files/test_data.csv'
nan = np.nan

# todo change handling of input dates to handle them all and sort it out
# todo remove metadata_mode from script, it should just be automatic
# todo add handling of wind run in mph there was only km
# todo update docs format on all functions, only have read config, validate file, and convert units so far
# todo check to see if a resolution of 1e-3 is good enough
# todo update rest of code to use config_dict
# todo make date input section of config file more verbose
# todo check cutoff of rhmax/min before ea calc

# First: CIMIS data from station 6 (Davis) on 8/18/18-8/22/18, no rain
# Second: CIMIS data from station 250 (Williams) on 9/15/16-9/19/16, no rain
# Third: CoAgMet data from station CTR02 (Coors Research Farm) on 8/18/18-8/22/18, no rain
# Fourth: CoAgMet data from station WLS01 (Plainsman Research Center) on 5/1/17-5/6/17, rain on 5/2/17 (index 1)
humidity_data = [
    [
        np.array([1.29, 1.32, 1.41, 1.49, 1.55]),  # Ea kpa
        np.array([36.78, 34.89, 31.0, 25.33, 28.56]),  # Tmax C
        np.array([12.33, 12.78, 11.39, 12.17, 12.61]),  # Tmin C
        np.array([24.33, 22.83, 20.55, 18.33, 19.72]),  # Tavg C
        np.array([10.78, 11.11, 12.00, 12.89, 13.50]),  # Tdew C
        np.array([80.0, 83.0, 86.0, 87.0, 94.0]),  # RHmax %
        np.array([20.0, 15.0, 32.0, 50.0, 41.0]),  # RHmin %
        np.array([43.0, 47.0, 58.0, 71.0, 67.0])  # RHavg %
    ], [
        np.array([1.37, 1.36, 1.48, 1.65, 1.69]),  # Ea kpa
        np.array([29.78, 33.45, 32.94, 34.17, 34.11]),  # Tmax C
        np.array([9.72, 10.0, 10.28, 13.06, 14.72]),  # Tmin C
        np.array([19.22, 20.39, 21.67, 23.5, 24.0]),  # Tavg C
        np.array([11.61, 11.50, 12.83, 14.5, 14.89]),  # Tdew C
        np.array([92.0, 91.0, 88.0, 86.0, 87.0]),  # RHmax %
        np.array([32.0, 29.0, 29.0, 33.0, 37.0]),  # RHmin %
        np.array([61.0, 57.0, 57.0, 57.0, 57.0])  # RHavg %
    ], [
        np.array([1.063, 0.77, 0.898, 1.101, 1.288]),  # Ea kpa
        np.array([24.99, 27.79, 26.88, 26.03, 23.81]),  # Tmax C
        np.array([8.11, 4.71, 3.795, 8.12, 8.57]),  # Tmin C
        np.array([16.24, 15.95, 15.77, 15.83, 14.87]),  # Tavg C
        np.array([nan, nan, nan, nan, nan]),  # Tdew C
        np.array([95.8, 94.7, 94.7, 90.6, 99.4]),  # RHmax %
        np.array([27.2, 12.2, 16.7, 26.5, 36.6]),  # RHmin %
        np.array([nan, nan, nan, nan, nan])  # RHavg %
    ], [
        np.array([0.673, 0.775, 0.835, 0.708, 0.902, 0.991]),  # Ea kpa
        np.array([13.34, 11.66, 12.2, 19.53, 25.06, 28.32]),  # Tmax C
        np.array([0.766, 2.303, 1.296, 0.57, 3.699, 7.79]),  # Tmin C
        np.array([5.998, 6.439, 6.62, 10.17, 14.5, 18.01]),  # Tavg C
        np.array([nan, nan, nan, nan, nan, nan]),  # Tdew C
        np.array([89.6, 100.4, 101.7, 89.9, 94.3, 89.1]),  # RHmax %
        np.array([56.0, 62.4, 51.7, 27.1, 26.3, 19.9]),  # RHmin %
        np.array([nan, nan, nan, nan, nan, nan])  # RHavg %
    ]]


def test_validate_file():
    """Check to see if input_functions.validate_file works on both test files"""
    # This has no assertions, it will raise an exception if a problem is found
    input_functions.validate_file(config_file_path, ['ini'])  # Test the config file
    input_functions.validate_file(data_file_path, ['csv'])  # Test the data file
    input_functions.validate_file(metadata_file_path, ['xls', 'xlsx'])  # Test the metadata file


def test_read_config():
    """Check to see if input_functions.read_config can open config file and find all required variables within it"""
    input_functions.read_config(config_file_path)


def test_temperature_conversion():
    """Check to see if input_functions.convert_units produces the expected values when converting temperature"""

    # Convert_units expects input in the form of numpy arrays
    temp_f = np.array([212.0])  # boiling point and freezing point of water in F
    temp_k = np.array([373.15])  # boiling point and freezing point of water in K
    temp_c = np.array([100.0])  # boiling point and freezing point of water in C

    config_dict_for_f = {'temp_f_flag': 1, 'temp_k_flag': 0}
    config_dict_for_k = {'temp_f_flag': 0, 'temp_k_flag': 1}
    config_dict_for_c = {'temp_f_flag': 0, 'temp_k_flag': 0}

    converted_temp_f_to_c = input_functions.convert_units(config_dict_for_f, temp_f, 'temperature')
    converted_temp_k_to_c = input_functions.convert_units(config_dict_for_k, temp_k, 'temperature')
    converted_temp_c_to_c = input_functions.convert_units(config_dict_for_c, temp_c, 'temperature')

    assert converted_temp_f_to_c[0] == pt.approx(temp_c[0], abs=1e-3),\
        'Temperature F to C and test value C are not equal.'
    assert converted_temp_k_to_c[0] == pt.approx(temp_c[0], abs=1e-3),\
        'Temperature K to C and test value C are not equal.'
    assert converted_temp_c_to_c[0] == pt.approx(temp_c[0], abs=1e-3),\
        'Temperature C to C and test value C are not equal.'


def test_wind_speed_conversion():
    """Check to see if input_functions.convert_units produces the expected values when converting windspeed"""

    # Convert_units expects input in the form of numpy arrays
    uz_mph = np.array([15.66])  # Test wind in miles per hour
    uz_run_mi = np.array([375.8])  # Test speed in daily wind run (miles)
    uz_run_km = np.array([604.80])  # Test speed in daily wind run (kilometers)
    uz_ms = np.array([7.0])  # Test wind speed in meters per second

    config_dict_for_mph = {'uz_mph_flag': 1, 'uz_wind_run_km_flag': 0, 'uz_wind_run_mi_flag': 0}
    config_dict_for_run_km = {'uz_mph_flag': 0, 'uz_wind_run_km_flag': 1, 'uz_wind_run_mi_flag': 0}
    config_dict_for_run_mi = {'uz_mph_flag': 0, 'uz_wind_run_km_flag': 0, 'uz_wind_run_mi_flag': 1}
    config_dict_for_ms = {'uz_mph_flag': 0, 'uz_wind_run_km_flag': 0, 'uz_wind_run_mi_flag': 0}

    converted_uz_mph_to_ms = input_functions.convert_units(config_dict_for_mph, uz_mph, 'wind_speed')
    converted_uz_run_km_to_ms = input_functions.convert_units(config_dict_for_run_km, uz_run_km, 'wind_speed')
    converted_uz_run_mi_to_ms = input_functions.convert_units(config_dict_for_run_mi, uz_run_mi, 'wind_speed')
    converted_uz_ms_to_ms = input_functions.convert_units(config_dict_for_ms, uz_ms, 'wind_speed')

    assert converted_uz_mph_to_ms[0] == pt.approx(uz_ms[0], abs=1e-3), \
        'Wind mph to m/s and test value m/s are not equal.'
    assert converted_uz_run_km_to_ms[0] == pt.approx(uz_ms[0], abs=1e-3), \
        'Wind run_km to m/s and test value m/s are not equal.'
    assert converted_uz_run_mi_to_ms[0] == pt.approx(uz_ms[0], abs=1e-3), \
        'Wind run_mi to m/s and test value m/s are not equal.'
    assert converted_uz_ms_to_ms[0] == pt.approx(uz_ms[0], abs=1e-3), \
        'Wind m/s to m/s and test value m/s are not equal.'


def test_vapor_pressure_conversion():
    """Check to see if input_functions.convert_units produces the expected values when converting vapor pressure"""

    # Convert_units expects input in the form of numpy arrays
    ea_torr = np.array([7.5])  # Test vapor pressure in torr or mmhg
    ea_mbar = np.array([10.0])  # Test vapor pressure in millibars
    ea_kpa = np.array([1.0])  # Test vapor pressure in kilopascals

    config_dict_for_torr = {'ea_torr_flag': 1, 'ea_mbar_flag': 0}
    config_dict_for_mbar = {'ea_torr_flag': 0, 'ea_mbar_flag': 1}
    config_dict_for_kpa = {'ea_torr_flag': 0, 'ea_mbar_flag': 0}

    converted_ea_torr_to_kpa = input_functions.convert_units(config_dict_for_torr, ea_torr, 'vapor_pressure')
    converted_ea_mbar_to_kpa = input_functions.convert_units(config_dict_for_mbar, ea_mbar, 'vapor_pressure')
    converted_ea_kpa_to_kpa = input_functions.convert_units(config_dict_for_kpa, ea_kpa, 'vapor_pressure')

    assert converted_ea_torr_to_kpa[0] == pt.approx(ea_kpa[0], abs=1e-3), \
        'Ea torr to kpa and test value kpa are not equal.'
    assert converted_ea_mbar_to_kpa[0] == pt.approx(ea_kpa[0], abs=1e-3), \
        'Ea mbar to kpa and test value kpa are not equal.'
    assert converted_ea_kpa_to_kpa[0] == pt.approx(ea_kpa[0], abs=1e-3), \
        'Ea kpa to kpa and test value kpa are not equal.'


def test_solar_radiation_conversion():
    """Check to see if input_functions.convert_units produces the expected values when converting solar radiation"""

    # Convert_units expects input in the form of numpy arrays
    rs_lang = np.array([206.363])  # Test radiation in langleys
    rs_mj = np.array([8.640])  # Test radiation in megajoules/m2
    rs_kwhr = np.array([2.4])  # Test radiation in kilowatt-hours/m2
    rs_w = np.array([100.0])  # Test radiation in watts/m2

    config_dict_for_lang = {'rs_lang_flag': 1, 'rs_mj_flag': 0, 'rs_kwhr_flag': 0}
    config_dict_for_mj = {'rs_lang_flag': 0, 'rs_mj_flag': 1, 'rs_kwhr_flag': 0}
    config_dict_for_kwhr = {'rs_lang_flag': 0, 'rs_mj_flag': 0, 'rs_kwhr_flag': 1}
    config_dict_for_w = {'rs_lang_flag': 0, 'rs_mj_flag': 0, 'rs_kwhr_flag': 0}

    converted_rs_lang_to_w = input_functions.convert_units(config_dict_for_lang, rs_lang, 'solar_radiation')
    converted_rs_mj_to_w = input_functions.convert_units(config_dict_for_mj, rs_mj, 'solar_radiation')
    converted_rs_kwhr_to_w = input_functions.convert_units(config_dict_for_kwhr, rs_kwhr, 'solar_radiation')
    converted_rs_w_to_w = input_functions.convert_units(config_dict_for_w, rs_w, 'solar_radiation')

    assert converted_rs_lang_to_w[0] == pt.approx(rs_w[0], abs=1e-3), \
        'Solar radiation lang to w/m2 and test value w/m2 are not equal.'
    assert converted_rs_mj_to_w[0] == pt.approx(rs_w[0], abs=1e-3), \
        'Solar radiation mj/m2 to w/m2 and test value w/m2 are not equal.'
    assert converted_rs_kwhr_to_w[0] == pt.approx(rs_w[0], abs=1e-3), \
        'Solar radiation kw-hr/m2 to w/m2 and test value w/m2 are not equal.'
    assert converted_rs_w_to_w[0] == pt.approx(rs_w[0], abs=1e-3), \
        'Solar radiation w/m2 to w/m2 and test value w/m2 are not equal.'


def test_precipitation_conversion():
    """Check to see if input_functions.convert_units produces the expected values when converting precipitation"""

    # Convert_units expects input in the form of numpy arrays
    pp_inch = np.array([1.0])  # Test precipitation in inches
    pp_mm = np.array([25.4])  # Test precipitation in millimeters

    config_dict_for_inch = {'pp_inch_flag': 1}
    config_dict_for_mm = {'pp_inch_flag': 0}

    converted_pp_inch_to_mm = input_functions.convert_units(config_dict_for_inch, pp_inch, 'precipitation')
    converted_pp_mm_to_mm = input_functions.convert_units(config_dict_for_mm, pp_mm, 'precipitation')

    assert converted_pp_inch_to_mm[0] == pt.approx(pp_mm[0], abs=1e-3), \
        'Precipitation inch to mm and test value mm are not equal.'
    assert converted_pp_mm_to_mm[0] == pt.approx(pp_mm[0], abs=1e-3), \
        'Precipitation mm to mm and test value mm are not equal.'


def test_relative_humidity_conversion():
    """Check to see if input_functions.convert_units produces the expected values when converting relative humidity"""

    # Convert_units expects input in the form of numpy arrays
    rh_fract = np.array([0.5])  # Test relative humidity as a fraction
    rh_perct = np.array([50.0])  # Test relative humidity as a percentage

    config_dict_for_fract = {'rh_fraction_flag': 1}
    config_dict_for_perct = {'rh_fraction_flag': 0}

    converted_rh_fract_to_perct = input_functions.convert_units(config_dict_for_fract, rh_fract, 'relative_humidity')
    converted_rh_perct_to_perct = input_functions.convert_units(config_dict_for_perct, rh_perct, 'relative_humidity')

    assert converted_rh_fract_to_perct[0] == pt.approx(rh_perct[0], abs=1e-3), \
        'Relative humidity fraction to percentage and test value percentage are not equal.'
    assert converted_rh_perct_to_perct[0] == pt.approx(rh_perct[0], abs=1e-3), \
        'Relative humidity percentage to percentage and test value percentage are not equal.'


@pt.mark.parametrize("ea,tmax,tmin,tavg,tdew,rhmax,rhmin,rhavg", humidity_data)
def test_ea_calculations(ea, tmax, tmin, tavg, tdew, rhmax, rhmin, rhavg):
    """test calculating ea from the various humidity variables"""

    # Columns for ea from ea
    tdew_col, rhmax_col, rhmin_col, rhavg_col = -1, -1, -1, -1
    ea_col = 1
    ea_from_ea, tdew_from_ea = data_functions.calc_humidity_variables(tmax, tmin, tavg, ea, ea_col, tdew, tdew_col,
                                                                      rhmax, rhmax_col, rhmin, rhmin_col, rhavg,
                                                                      rhavg_col)
    # Ea from TDew
    if np.isnan(tdew).all():  # all of tdew is nans, so it wasn't present in original dataset
        ea_from_tdew = None
        tdew_from_tdew = None
    else:
        # Columns for ea from tdew
        ea_col, rhmax_col, rhmin_col, rhavg_col = -1, -1, -1, -1
        tdew_col = 1

        ea_from_tdew, tdew_from_tdew = data_functions\
            .calc_humidity_variables(tmax, tmin, tavg, ea, ea_col, tdew, tdew_col, rhmax, rhmax_col,
                                     rhmin, rhmin_col, rhavg, rhavg_col)

        ea_from_tdew_prct_diff = np.nanmean(((ea_from_tdew - ea) / ea) * 100.0)
        print('\nPercentage difference from ea from tdew')
        print(ea_from_tdew_prct_diff)

    # Ea from RHMax and RHMin
    if np.isnan(rhmax).all():  # all of rhmax is nans, so it wasn't present in the original dataset
        ea_from_rhmax_rhmin = None
        tdew_from_rhmax_rhmin = None
    else:
        # Columns for ea from rhmax/rhmin
        ea_col, tdew_col, rhavg_col = -1, -1, -1
        rhmax_col, rhmin_col = 1, 1

        ea_from_rhmax_rhmin, tdew_from_rhmax_rhmin = data_functions\
            .calc_humidity_variables(tmax, tmin, tavg, ea, ea_col, tdew, tdew_col, rhmax,
                                     rhmax_col, rhmin, rhmin_col, rhavg, rhavg_col)

        ea_from_rhmaxmin_prct_diff = np.nanmean(((ea_from_rhmax_rhmin - ea) / ea) * 100.0)
        print('\nPercentage difference from ea from rhmaxmin')
        print(ea_from_rhmaxmin_prct_diff)

    # Ea from RHAvg
    if np.isnan(rhavg).all():  # all of rhavg is nans, so it wasn't present in the original dataset
        ea_from_rhavg = None
        tdew_from_rhavg = None
    else:
        # Columns for ea from rhavg
        ea_col, tdew_col, rhmax_col, rhmin_col = -1, -1, -1, -1
        rhavg_col = 1

        ea_from_rhavg, tdew_from_rhavg = data_functions\
            .calc_humidity_variables(tmax, tmin, tavg, ea, ea_col, tdew, tdew_col, rhmax,
                                     rhmax_col, rhmin, rhmin_col, rhavg, rhavg_col)

        ea_from_rhavg_prct_diff = np.nanmean(((ea_from_rhavg - ea) / ea) * 100.0)
        print('\nPercentage difference from ea from rhavg')
        print(ea_from_rhavg_prct_diff)

    test_eo_tmax = np.array(0.6108 * np.exp((17.27 * tmax) / (tmax + 237.3)))
    test_eo_tmin = np.array(0.6108 * np.exp((17.27 * tmin) / (tmin + 237.3)))
    test_eo_tavg = np.array(0.6108 * np.exp((17.27 * tavg) / (tavg + 237.3)))

    test_ea_from_rhavg = np.array((test_eo_tavg * (rhavg / 100)))
    test_ea_from_rhmaxmin = np.array(((test_eo_tmin * (rhmax / 100)) + (test_eo_tmax * (rhmin / 100))) / 2)

    if not np.isnan(rhmax).all():
        assert test_ea_from_rhmaxmin[0] == ea_from_rhmax_rhmin[0]
        assert test_ea_from_rhmaxmin[1] == ea_from_rhmax_rhmin[1]
        assert test_ea_from_rhmaxmin[2] == ea_from_rhmax_rhmin[2]
        assert test_ea_from_rhmaxmin[3] == ea_from_rhmax_rhmin[3]
        assert test_ea_from_rhmaxmin[4] == ea_from_rhmax_rhmin[4]

    if not np.isnan(rhavg).all():
        assert test_ea_from_rhavg[0] == ea_from_rhavg[0]
        assert test_ea_from_rhavg[1] == ea_from_rhavg[1]
        assert test_ea_from_rhavg[2] == ea_from_rhavg[2]
        assert test_ea_from_rhavg[3] == ea_from_rhavg[3]
        assert test_ea_from_rhavg[4] == ea_from_rhavg[4]

def blank():
    pass
