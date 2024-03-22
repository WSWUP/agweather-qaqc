agweather-qaqc (Weather Data QAQC Script)
==============================================
``agweather-qaqc`` provides a flexible workflow for the visualization, review, and QAQC of daily weather data. This script intended to be used as an early step in any analysis that might use daily sources of agricultural weather data, particularly for projects with an interest in reference evapotranspiration (ET) data, or where observational data are considered to be 'truth' when evaluating model predictions. ``agweather-qaqc`` is command-line interface driven, and provides reminders, prompts, and recommendations to assist users who may not be overly proficient with Python.

Functionalities include:
* Importing data without having to convert it to a standardized format, with unit conversions based on a user-specified configuration file.
* Converting multiple input formats from separate sources or networks into a single, uniform format for easier downstream analysis.
* Visualizing data before and after processing with interactive plots, as daily time series and as mean monthly averages.
* Filtering and removal of data, both manually and automatically, with statistics-based approaches to identify and correct issues such as sensor miscalibration.
* Calculation of [theoretical clear-sky solar radiation](https://wswup.github.io/agweather-qaqc/_static/asce_refet_appendices.pdf) and [Thornton-Running solar radiation](https://wswup.github.io/agweather-qaqc/_static/thornton_running_1997.pdf).
* Calculation of grass and alfalfa reference ET according to the [American Society of Civil Engineers Standardized reference evapotranspiration equation](https://wswup.github.io/agweather-qaqc/_static/asce_refet_publication.pdf) via the [RefET](https://github.com/WSWUP/RefET) library.
* Evaluating station aridity through the visualization of both relative humidity and dew point depression plots.
* Optional gap-filling of data using station climatologies, empirical approaches (e.g. Thornton-Running solar), or random sampling.

Documentation
-------------

[Github Page](https://wswup.github.io/agweather-qaqc/)

Installation
------------

1. Clone the repository:

    ```
    git clone https://github.com/WSWUP/agweather-qaqc
    ```
2. Navigate the command line/terminal into the repository root directory:
    ```
    cd path/to/agweatherqaqc
    ```
3. Setting up and activating the environment can be done one of three ways:
   * Conda Environment:
     ```
     conda env create -f environment.yml
     ```
     ```
     activate agweatherqaqc
     ```
   * Pipenv Environment:
     ```
     pipenv install -r requirements.txt
     ```
     ```
     pipenv shell
     ```
   * PDM Environment:
     ```
     pdm install
     ```
     ```
     pdm shell
     ```

4. Run the script via the file ``qaqc_single_station.py``
    ```
    python qaqc_single_station.py <OPTIONAL ARGUMENTS>
    ```

See the [documentation](https://wswup.github.io/agweather-qaqc/) for more information.
