[![DOI](https://joss.theoj.org/papers/10.21105/joss.06368/status.svg)](https://doi.org/10.21105/joss.06368)

agweather-qaqc (Weather Data QAQC Script)
==============================================

> **Version note:** ``agweather-qaqc`` **v0.7.0** was used to generate the
> [CONUS-AgWeather dataset](https://doi.org/10.5281/zenodo.18122156). This branch
> preserves that workflow for reproducibility. For general use, please always
> refer to the [latest release](https://github.com/WSWUP/agweather-qaqc/releases).

``agweather-qaqc`` provides a flexible workflow for the visualization, review, and QAQC of daily weather data. This script is intended to be used as an early step in any analysis that might use daily sources of agricultural weather data, particularly for projects with an interest in reference evapotranspiration (ET) data, or where observational data are considered to be 'truth' when evaluating model predictions. ``agweather-qaqc`` is command-line interface driven, and provides reminders, prompts, and recommendations to assist users who may not be overly proficient with Python.

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

> **Python version:** This branch (used for CONUS-AgWeather v0.7.0) was developed
> and tested on **Python 3.7**, with package versions pinned in
> ``requirements.txt`` to those current as of March 2020. Newer Python releases
> may require dependency upgrades; please refer to the
> [latest release](https://github.com/WSWUP/agweather-qaqc/releases) for current
> Python compatibility.

> **Apple Silicon (M1/M2/M3) macOS:** the 2020 package pins do not have native
> ``osx-arm64`` wheels (numpy 1.18.2, pandas 1.0.3, bokeh 2.0.0 all predate
> Apple Silicon). Create the conda environment under x86_64 / Rosetta instead:
>
> ```
> CONDA_SUBDIR=osx-64 conda create -n agweatherqaqc python=3.8 -y
> conda activate agweatherqaqc
> conda config --env --set subdir osx-64
> pip install -r requirements.txt
> ```
>
> The ``conda config --env --set subdir osx-64`` line pins the env to Intel
> builds so future ``conda install`` calls also pull x86_64 wheels. Python 3.8
> is used here because no ``osx-arm64`` Python 3.7 build exists on conda-forge;
> the package pins are compatible with both 3.7 and 3.8.

1. Clone the repository:

    ```
    git clone https://github.com/WSWUP/agweather-qaqc
    ```
2. Navigate the command line/terminal into the repository root directory:
    ```
    cd path/to/agweather-qaqc
    ```
3. Setting up and activating the environment can be done one of three ways:
   * Conda Environment:
     ```
     conda env create -f environment.yml
     ```
     ```
     conda activate agweatherqaqc
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
