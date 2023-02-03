from qaqc_modules.py_weather_qaqc import WeatherQAQC
import sys


if __name__ == "__main__":
    # This code sets up the WeatherQAQC class to handle a single station
    # Initial setup
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

    station_qaqc = WeatherQAQC(config_path, metadata_path, gridplot_columns=1)
    station_qaqc.process_station()
    print("\nSystem: Now ending single station QAQC script.")
