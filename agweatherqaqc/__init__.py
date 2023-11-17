"""
A package for the correction of sensor drift and removal of bad data for weather stations.
The process is CLI-driven and provides recommendations to the user for best practices.

Also generates Reference Evapotranspiration according to the ASCE Evapotranspiration Equation (2005)
"""

__name__ = 'agweatherqaqc'
__author__ = 'Christian Dunkerly'
__version__ = '1.0.1'

from agweatherqaqc import agweatherqaqc
from agweatherqaqc import calc_functions
from agweatherqaqc import input_functions
from agweatherqaqc import plotting_functions
from agweatherqaqc import qaqc_functions
from agweatherqaqc import utils
