agweatherqaqc package
=====================

Package Contents
----------------

.. automodule:: agweatherqaqc
   :members:
   :undoc-members:
   :show-inheritance:

This package is meant to be run by creating an instance of the `agweatherqaqc.WeatherQC` class and
then calling `process_station()`, which handles running the workflow. From this point the user
directs everything else through interactive prompts in the command line / terminal window.

Example:
    >>> from agweatherqaqc.agweatherqaqc import WeatherQC
    >>> config_path = 'test_files/test_config.ini'
    >>> metadata_path = 'test_files/test_metadata.xlsx'
    >>> station_qaqc = WeatherQC(config_path, metadata_path, gridplot_columns=1)
    >>> station_qaqc.process_station()

The documentation on the rest of the correction and calculation functions is available to explain
the methodology and thought process that went into them.

agweatherqaqc.agweatherqaqc
----------------------------------

.. automodule:: agweatherqaqc.agweatherqaqc
   :members:
   :undoc-members:
   :show-inheritance:

agweatherqaqc.calc\_functions
------------------------------------

.. automodule:: agweatherqaqc.calc_functions
   :members:
   :undoc-members:
   :show-inheritance:

agweatherqaqc.qaqc\_functions
------------------------------------

.. automodule:: agweatherqaqc.qaqc_functions
   :members:
   :undoc-members:
   :show-inheritance:

agweatherqaqc.utils
--------------------------

.. automodule:: agweatherqaqc.utils
   :members:
   :undoc-members:
   :show-inheritance:
