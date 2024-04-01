from agweatherqaqc.agweatherqaqc import WeatherQC
import sys


if __name__ == "__main__":
    # This code sets up the WeatherQAQC class to handle a single station
    # it can be used as either the primary way of running this code
    # or it can serve as an example of how to make calls to the AgWeatherQAQC class

    # Check if python version is acceptable
    if sys.version_info.major == 3 and sys.version_info.minor >= 9:
        pass
    else:
        raise SystemError(
            f'\n\nagweatherqaqc requires a python version between 3.9.X and 3.X.X. \n'
            f'The current version of python being run is {sys.version}. \n\n')

    # Check if user has passed in a config file, or else just grab the default.
    # Also see if user has passed a metadata file to allow for automatic reading/writing into the metadata file.
    if len(sys.argv) == 2:
        config_path = sys.argv[1]
        metadata_path = None
    elif len(sys.argv) == 3:
        config_path = sys.argv[1]
        metadata_path = sys.argv[2]
    else:
        config_path = 'tests/test_files/test_config.ini'
        metadata_path = None
        print(f"\nSystem: no configuration file provided, using test config file located at \'{config_path}\'.\n"
              f"     To use your own configuration file, specify it when running qaqc_single_station.py like so: \n"
              f"\'python qaqc_single_station.py PATH/TO/CONFIG.INI\'\n")

    print("\nSystem: Starting single station data QAQC script.")
    station_qaqc = WeatherQC(config_path, metadata_path, gridplot_columns=1)
    station_qaqc.process_station()
    print("\nSystem: Now ending single station QAQC script.")
