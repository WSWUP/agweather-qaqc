"""
A package for the correction of sensor drift and removal of bad/suspect data for weather stations.
The process is CLI-driven and provides recommendations to the user for best practices.

Also generates Reference Evapotranspiration according to the ASCE Evapotranspiration Equation (2005).
"""

__name__ = 'agweatherqaqc'
__author__ = 'Christian Dunkerly'
__version__ = '1.0.3'

from agweatherqaqc import agweatherqaqc
from agweatherqaqc import utils
from agweatherqaqc import calc_functions
from agweatherqaqc import input_functions
from agweatherqaqc import plot
from agweatherqaqc import qaqc_functions
