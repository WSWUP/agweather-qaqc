
agweather-qaqc - Interactive Graphical Weather Data Correction
==============================================================

Flexible, command-line-driven software to QC daily weather data and then calculate reference
evapotranspiration according to the `ASCE (2005) method <_static/asce_refet_publication.pdf>`_.


This package was designed to visualize weather variable time series data to enable rapid human data assessment and pattern recognition. The observation data are displayed in
`Bokeh <https://github.com/bokeh/bokeh>`_ time series plots both before and after adjustment via the QAQC process,
enabling users to readily visualize and assess data patterns and trends related to sensor drift,
probable miscalibration, data outliers, sensor malfunction, etc. These plots are accompanied by interactive
tools (ex. pan and zoom controls, display info on hover), and feature linked axes, allowing the user to
readily visualize and assess how variables vary and covary over time and at different time scales
(e.g. daily, monthly, annual). These graphs are saved as stand-alone HTML files to allow for
easy sharing of results.

While ease-of-use for a non-technical user was one of the principle goals, the software workflow can be
automated with the inclusion of libraries such as `PyAutoGUI <https://github.com/asweigart/pyautogui>`_.

**The agweather-qaqc package features include:**

* Importing daily observational data without having to convert it to a standardized format, with unit conversions based on a user-specified configuration file.
* Converting multiple input formats from separate sources or networks into a single, uniform format for easier downstream analysis.
* Visualizing data before and after processing with interactive plots, as daily time series and as mean monthly averages.
* Filtering and removal of data, both manual and automatic, with statistics-based approaches to identify and correct issues such as sensor miscalibration.
* Calculation of theoretical clear-sky solar radiation using date, location and elevation information along with humidity data based on `ASCE standardizations <_static/asce_refet_appendices.pdf>`_.
* Calculation of expected solar radiation using the empirical `Thornton-Running <_static/thornton_running_1997.pdf>`_ approach with Monte-Carlo optimized empirical parameters based on observed solar radiation data.
* Calculation of the daily dew point depression (i.e., daily minimum temperature minus daily average dew point temperature) used to assess whether the data collection environment included a well-watered surface having expected feedbacks on near-surface humidity and air temperature.
* Calculation of grass and alfalfa reference evapotranspiration according to the American Society of Civil Engineers (ASCE) `Standardized Reference Evapotranspiration equation <_static/asce_refet_publication.pdf>`_ via the `RefET <https://github.com/WSWUP/RefET>`_ library.
* Evaluating station aridity through the visualization of both relative humidity and dew point depression plots, with the option to adjust relative humidity if required.
* Optional gap-filling of data using station climatologies, empirical approaches (e.g. Thornton-Running solar), or random sampling from distributions based on previous observations, resulting in a complete record of daily reference evapotranspiration for cumulative monthly and annual totals.
* Creating archival charts and log files that record and flag how each variable was changed during the QAQC process.

.. note::
   agweather-qaqc was developed for daily weather data. Support for sub-daily data may be added eventually.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   data_preparation
   qc_information
   modules



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
