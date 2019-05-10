from qaqc_modules.py_weather_qaqc import WeatherQAQC
import sys


if __name__ == "__main__":
    # This code sets up the WeatherQAQC class to handle a single station

    # Initial setup
    # Check if user has passed in a config file, or else just grab the default.
    print("\nSystem: Starting single station data QAQC script.")
    if len(sys.argv) == 2:
        config_path = sys.argv[1]
    else:
        config_path = 'config.ini'

    station_qaqc = WeatherQAQC(config_path, None)
    test_change = 1

    print("\nSystem: Now ending single station QAQC script.")
