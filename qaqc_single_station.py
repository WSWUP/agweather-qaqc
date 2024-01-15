from agweatherqaqc.agweatherqaqc import WeatherQC
import sys


if __name__ == "__main__":
    # This code sets up the WeatherQAQC class to handle a single station
    # it can be used as either the primary way of running this code
    # or it can serve as an example of how to make calls to the AgWeatherQAQC class

    # Check if python version is acceptable
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 9):
        raise SystemError(
            f'\n\nagweatherqaqc requires a python version of 3.9.17 or newer. \n'
            f'The current version of python being run is {sys.version}. \n\n')
    elif sys.version_info.major > 3 or (sys.version_info.major == 3 and sys.version_info.minor > 11):
        print(
            f'\n\nag-weather-qaqc has been tested on python versions 3.9.17 through 3.11.X. \n' 
            f'The current version of python being run is {sys.version}. \n\n'
            f'The script will likely still function, but spend extra time verifying outputs.')
    else:
        pass

    # Check if user has passed in a config file, or else just grab the default.
    # Also see if user has passed a metadata file to allow for automatic reading/writing into the metadata file.
    print("\nSystem: Starting single station data QAQC script.")
    if len(sys.argv) == 2:
        config_path = sys.argv[1]
        metadata_path = None
    elif len(sys.argv) == 3:
        config_path = sys.argv[1]
        metadata_path = sys.argv[2]
    else:
        config_path = 'config.ini'
        metadata_path = None


    station_qaqc = WeatherQC(config_path, metadata_path, gridplot_columns=1)
    station_qaqc.process_station()
    print("\nSystem: Now ending single station QAQC script.")
