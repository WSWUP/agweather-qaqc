from __future__ import division
import warnings
import numpy as np

# Calculate Rso and Thornton Running Rs
def emprso_w_tr(lat, press, ea, jul, delta_t, tm_tm):
    from math import sin, pi, exp, acos, tan, cos
    # lat - station latitude in decimal degrees
    # press - pressure at station in kPa
    # ea - actual vapor pressure in kPa
    # jul - day of year
    # delta_t - mean monthly tmax_tmin difference
    # tm_tm - tmax_tmin difference

    # sda - solar declination angle
    # gsc - solar constant, units mJm^-2h^-1
    # ktb - atmospheric clearness coefficient
    # w - precipitable water, eqn 22
    # kt - atmospheric transmissivity
    # dr - squared inverse relative distance factor

    # ra - exoatmospheric solar radiation
    # rso - theoretical solar radiation

    # b - empirical fitting coefficient for TR
    # emp_rs - empirical thornton running solar radiation

    # Outputs rso and rs_tr in MJ m-2

    gsc = 4.92
    ktb = 0.9
    w = 0.14 * ea * press + 2.1

    sinb24 = sin(0.85 + 0.3 * (lat * (pi / 180)) * sin(((2 * pi) / 365) * jul - 1.39) - 0.42 * (lat * (pi / 180)) ** 2)

    kb = 0.98 * exp(((-.00146 * press) / (ktb * sinb24)) - 0.075 * (w / sinb24) ** 0.4)

    sda = 0.409 * sin(2 * pi * jul / 365 - 1.39)

    if kb > 0.15:
        kd = 0.35 - 0.36 * kb  # equation 23, index of transmissivity for diffuse radiation.
    else:
        kd = 0.18 + 0.82 * kb  # equation 23, index of transmissivity for diffuse radiation.

    kt = kb + kd

    ws = acos(-1 * tan((lat * (pi / 180))) * tan(sda))

    dr = 1 + 0.033 * cos((2 * pi / 365) * jul)

    ra = 24 / pi * gsc * dr * (ws * sin(lat * (pi / 180)) * sin(sda) + cos(lat * (pi / 180)) * cos(sda) * sin(ws))

    rso = kt * ra  # equation 16

    b = 0.031 + 0.201 * exp(-0.185 * delta_t)  # equation 15

    emp_rs = np.nan
    # Text below is to catch the "Invalid value encountered in double scalar" runtime warning
    # Error pops up when tm_tm is a NaN (so data point needs to be discarded anyways) and impacts
    # a small number of data points (7 days out of approximately 6500 in test dataset)
    # incidences of error are reported to the log file
    with warnings.catch_warnings():
        warnings.filterwarnings('once')
        try:
            emp_rs = rso * (1 - 0.9 * exp(-1 * b * tm_tm ** 1.5))
        except Warning as e:
            print('\nRunTime error found calculating emp_rs:', e)
            print('Tmax-Tmin value was :', tm_tm)

    return rso, emp_rs


# Calculate ETrs or ETos based on passed in parameters
# Take care to make sure correct 'ref' and 'wind_adjust' parameters are being passed in
def asce_refet(t_max, t_min, solar, wind, ref, wind_adjust, jul, lat, elev, *args):
    from math import sin, pi, exp, acos, tan, cos, log, sqrt
    # Computes ASCE standardized reference ET on daily timestep
    # Inputs:
    # t_max - daily max temperature in C
    # t_min - daily min temperature in C
    # solar - solar shortwave radiation in w/m^2
    # wind - wind speed in m/s
    # ref - reference value, 1 for short (grass) 0 for long (alphalpha)
    # wind_adjust - 1,2,3 for 10m, 3m, or 2m respectively
    # jul - julian day of year
    # lat - station latitude (decimal degrees)
    # elev - station elevation in meters
    #
    # *args - can run using tdew or RHmax and RHmin
    # for tdew include it as the last argument at the end
    # tdew must be in celcius
    # for RH include max THEN min at the end
    #
    # Output: daily reference et in MM/Day
    #
    # Original Author: Dan McEvoy / Justin Huntington
    # Last Updated 04/02/2014
    # Translated to Python 02/2017

    # Adjust windspeed if needed
    if wind_adjust == 1:  # 10m
        u2 = wind * (4.87 / log((67.8 * 10) - 5.42))
    elif wind_adjust == 2:  # 3m
        u2 = wind * (4.87 / log((67.8 * 3) - 5.42))
    else:
        u2 = wind  # 2m

    # create secondary variables
    tmean = (t_max + t_min) / 2
    es_tmax = 0.6108 * exp((17.27 * t_max) / (t_max + 237.3))  # saturation vapor pressure (kPa) at tmax
    es_tmin = 0.6108 * exp((17.27 * t_min) / (t_min + 237.3))  # saturation vapor pressure (kPa) at tmin
    es_tmean = 0.6108 * exp((17.27 * tmean) / (tmean + 237.3))  # saturation vapor pressure (kPa) at tmean
    es = (es_tmax + es_tmin) / 2  # daily mean saturation vapor pressure

    delta_slope = np.nan
    # Text below is to catch the "Invalid value encountered in double scalar" runtime warning
    # Error pops up when dependant variables are a NaN (so data point needs to be discarded anyways) and impacts
    # a small number of data points (7 days out of approximately 6500 in test dataset)
    # incidences of error are reported to the log file
    with warnings.catch_warnings():
        warnings.filterwarnings('once')
        try:
            delta_slope = (
                (4098 * es_tmean) / ((tmean + 237.3) ** 2))  # slope of the saturation vapor press curve at avg temp
        except Warning as e:
            print('\nRunTime error found calculating delta_slope:', e)
            print('es_tmean value was :', es_tmean)
            print('tmean value was :', tmean)

    g = 0  # G=soil heat flux density in MJm-2d-1

    # Solar radiation calculations
    gsc = 0.082  # solar constant
    sig = 4.90 * 10 ** -9  # Sigma, Steffan-Boltzman constant
    phi = (pi * lat) / 180  # convert latitude from degrees to radians
    pressure = 101.3 * ((293 - 0.0065 * elev) / 293) ** 5.26  # kPA
    lamda = 2.45  # latent heat of vaporization MJ kg-1
    psyc = 0.00163 * (pressure / lamda)  # psychometric constant in kPa/C

    # vap_prs = actual vapor pressure (kPa) as a function relative humidity or dewpoint temperature
    if len(args) == 1:
        # calculate using tdew
        t_dew = args[0]
        # below equation sourced from http://agsys.cra-cin.it/tools/evapotranspiration/help/Actual_vapor_pressure.html
        vap_prs = 0.6108 * exp((17.27 * t_dew) / (t_dew + 237.3))
    elif len(args) == 2:
        # calculate using rh max and rh min
        rh_max = args[0]
        rh_min = args[1]
        vap_prs = (es_tmax * (rh_min / 100) + es_tmin * (rh_max / 100)) / 2
    else:
        print('Incorrect number of args given to refET script')
        raise ValueError('Incorrect number of args given to refET script, check arguments within main script')

    # Extraterrestrial radiation (Ra) is calculated for each day using
    # the following equations from Duffie and Beckman(1980)
    # dr = Correction for eccentricity of Earth's orbit around the sun on julian
    # day of the year
    dr = 1 + 0.033 * cos(((2 * pi) / 365) * jul)

    # delta = declination of the sun above the celestial equator in radians on
    # julian day of the year
    delta = 0.40928 * sin(((2 * pi) / 365) * jul - 1.39435)

    # omega = sunrise hour angle in radians
    omega = acos(-tan(phi) * tan(delta))

    # ra = extraterrestrial radiation (MJ m-2 d-1)
    ra = ((24 * 60) / pi) * gsc * dr * (omega * sin(delta) * sin(phi) + cos(phi) * cos(delta) * sin(omega))

    # precipitable water
    w = 0.14 * vap_prs * pressure + 2.1

    # angle of sun above horizon
    theta_24 = sin(0.85 + 0.3 * phi * sin(((2 * pi) / 365) * jul - 1.39) - 0.42 * phi ** 2)

    # kb, clearness index for direct beam radiation (unitless)
    kb = 0.98 * exp(((-0.00146 * pressure) / theta_24) - 0.075 * (w / theta_24) ** 0.4)

    # kd, transmissivity index for diffuse radiation (unitless)
    kd = 0.35 - 0.36 * kb

    # Rso = clear sky total global solar radiation at the Earth's surface in MJ m-2 d-1
    rso = (kb + kd) * ra

    # Rns = net solar radiation over grass as a function of measured solar
    # radiation (Rs) in MJ m-2 d-1
    rs = solar * 0.0864  # converting w/m2 into MJ/m2 per day
    rns = (1 - 0.23) * rs

    # f = a cloudiness function of Rs and Rso
    f = 1.35 * rs / rso - 0.35

    # net_emiss = apparent "net" clear sky emissivity
    net_emiss = 0.34 - 0.14 * sqrt(vap_prs)

    # rnl = Net Long Wave radiation in MJ m-2 d-1
    rnl = np.nan
    # Text below is to catch the "Invalid value encountered in double scalar" runtime warning
    # Error pops up when dependant variables are a NaN (so data point needs to be discarded anyways) and impacts
    # a small number of data points (7 days out of approximately 6500 in test dataset)
    # incidences of error are reported to the log file
    with warnings.catch_warnings():
        warnings.filterwarnings('once')
        try:
            rnl = f * net_emiss * sig * (((t_max + 273.15) ** 4 + (t_min + 273.15) ** 4) / 2)
        except Warning as e:
            print('\nRunTime error found calculating rnl:', e)
            print('f value was :', f)
            print('net_emiss value was :', net_emiss)
            print('sig value was :', sig)
            print('tmax value was :', t_max)
            print('tmin value was :', t_min)


    # Rn = Net Radiation over grass in MJ m-2 d-1
    rn = rns - rnl

    # Calculate ETo using the ASCE-EWRI (2005) standardized equation
    # determine short or long reference
    if ref == 1:  # short (ETo)
        cn = 900
        cd = 0.34
    else:  # long (ETr)
        cn = 1600
        cd = 0.38

    ref_et = (0.408 * delta_slope * (rn - g) + psyc * (cn / (tmean + 273)) * u2 * (es - vap_prs)) / (
                delta_slope + psyc * (1 + cd * u2))

    return ref_et

# This script is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of QAQC_Master.py, it does nothing by itself.")
