"""
A package for the correction of sensor drift and removal of bad data for weather stations.
The process is CLI-driven and provides recommendations to the user for best practices.

Also generates Reference Evapotranspiration according to the ASCE Evapotranspiration Equation (2005)
"""

__name__ = 'modules'
__author__ = 'Christian Dunkerly'
__version__ = '0.3.1'


from modules import data_functions
from modules import input_functions
from modules import plotting_functions
from modules import qaqc_functions
from modules import utils
