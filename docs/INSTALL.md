### Installation

Install pyWeatherQAQC by cloning its [GitHub repository](https://github.com/DRI-WSWUP/pyWeatherQAQC). The script is self-contained and is run locally, so the directory can be placed wherever you want it.  

### Python

pyWeatherQAQC is being developed for python 3.6, however it may work on python 2.7 with additional dependencies. Please see the dependencies section for more information.

### Dependencies
If you are running this script by itself, install the general dependencies. If you are using this script prior to running [pyMETRIC](https://github.com/DRI-WSWUP/pymetric), you only need to install the pyMETRIC dependencies.

#### General Dependencies: 
The script is dependent on the following python packages:
* [refet v0.3.5](https://github.com/DRI-WSWUP/RefET): Used to calculate reference evapotranspiration from provided data.
* [bokeh](https://bokeh.pydata.org/en/latest/): Used to dynamically plot weather data for viewing and correction.
* [numpy](http://www.numpy.org): Used for data processing.
* [pandas](https://www.pandas.pydata.org): Used for data processing.

#### pyMETRIC Dependencies:
* [bokeh](https://bokeh.pydata.org/en/latest/): Used to dynamically plot weather data for viewing and correction.
* [numpy](http://www.numpy.org): Used for data processing.

#### Additional Python 2 Dependencies
* [configparser (Python 3)](https://docs.python.org/3/library/configparser.html): Used to read in parameters from configuration file.
* [future](https://pypi.python.org/pypi/future): Brings the python 3 changes in math functions into python 2.

### Anaconda and Environments

Most of the required dependencies are included as part of the default [Anaconda](https://www.anaconda.com/download/) installation.

In addition to containing most of the required packages, Anaconda's environments allow for the creation of a dedicated environment to run this script. If you are using this script prior to running [pyMETRIC](https://github.com/DRI-WSWUP/pymetric), see the directions below for running this script on that environment.

For more help with using environments, please see the [Anaconda User Guide](https://conda.io/docs/user-guide/tasks/manage-environments.html).

#### General Conda Environment Setup

Create the environment:
```
> conda create -n pyweatherqaqc python=3.6 anaconda
```

Activate the newly created environment:
```
> activate pyweatherqaqc
```

The refet module is installed using pip:
```
> pip install refet --no-deps
```
The script is now ready to use. Remember to activate the environment (activate pyweatherqaqc) before running the script.

#### pyMETRIC Environment Setup
These directions assume you have already followed the installation instructions for pyMETRIC.

Activate your pyMETRIC environment:
```
> activate pymetric
```
Install the additional dependencies:
```
> conda install numpy bokeh
```
The script is now ready to use. Remember to activate the environment (activate pymetric) before running the script.
