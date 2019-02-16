# pyWeatherQAQC (Daily Weather Data QAQC Script)

## Edit (2/15/2019)
This script has recently undergone a major overhaul and the readme (and related files) still has to be updated. This newest version still works in the same fashion as the previous version.

### Summary
pyWeatherQAQC is a constantly-expanding python-based script that enables the user to:
1. Graphically visualize historical daily summary weather data from stations
2. Perform manual QA/QC on that data, with the option to specifically target intervals of problematic data
3. Calculate reference evapotranspiration using the ASCE-EWRI equation (see references).
4. Outputs all corrected and calculated data into a standardized layout, regardless of input data provided, to make downstream data processing or collation easier.

The script saves copies of all generated graphs and generates a log file that details what corrections were done for later reference.

### Installation
For detailed instructions on installing python, this script, required dependencies, and setting up a dedicated environment, please see the [installation instructions](docs/INSTALL.md).

### Data Setup
For instructions and an example on on setting up the data file and configuring the .ini file the script uses, please see the [data preparation instructions](docs/SETUP.md).

### Example Run

For an example workflow on correcting some data, see this [example workflow using the provided data](docs/EXAMPLERUN.md).

### Script Usage

The script expects to be called locally using the command prompt with the config, data, and module files organized according to the [data preparation instructions](docs/SETUP.md).

If you have the script located somewhere besides the C: drive, you will have to change drives first, which you can do with the command:
```
> <DRIVE_LETTER_HERE>:
```

Once you are on the correct drive, you can set the command prompt to the local directory by copying the text from the folder path in window's file explorer into the command prompt with the following command:
```
> cd <PATH_TEXT_HERE>
```

Once you are in the correct folder, you can run the script with the command:
```
> python QAQC_Master.py
```

#### Example of locating and running script:
In this example, the script was downloaded and placed at at Z:\scripts\pyWeatherQAQC, and the command prompt has just been opened:
```
C:\Users\Me> Z:
Z:\> cd Z:\scripts\pyWeatherQAQC
Z:\scripts\pyWeatherQAQC> python QAQC_Master.py
```

#### Limitations and Disclaimers
While the goal of the script is to improve the quality of data collected by remote sensing, it is still susceptible to the adage of, "garbage in, garbage out." Manually skimming over the generated graphs should be enough for you to see if something is amiss, but looking over the raw data is better. In addition, this script is still under development, so it is ultimately the responsibility of the end user to confirm the outputs as reasonable and correct.

The script will currently tackle the following problems with daily data:

* Removes impossible values or unreasonable values (such as negative wind speed)
* Resamples data should sections of the time series be missing (such as when data jumps from 1/5/2007 straight to 8/17/2017)
* Deletes multiple instances of a single day's data (the first instance is preserved)

If the input data has a problem not listed above, then the script will most likely not produce a usable result.


References
----------
* The ASCE-EWRI Standardized Reference Evapotranspiration Equation (2005) [Full Report](http://www.kimberly.uidaho.edu/water/asceewri/ascestzdetmain2005.pdf) and [Appendix](http://www.kimberly.uidaho.edu/water/asceewri/appendix.pdf)

