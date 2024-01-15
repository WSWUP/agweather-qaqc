import csv
import numpy as np
import pathlib as pl


# Background color to be used for all plots
BACKGROUND_COLOR = '#fafafa'

# This dictionary stores the variable names and plot features for each
#   variable/pair of variables that may be processed
FEATURES_DICT = {
    1: {"var_one_name": "Temperature Maximum",
        "var_one_color": "red",
        "var_two_name": "Temperature Minimum",
        "var_two_color": "blue",
        "units": "°C",
        "qc_filename": "tmax_tmin"},
    2: {"var_one_name": "Temperature Minimum",
        "var_one_color": "blue",
        "var_two_name": "Dewpoint Temperature",
        "var_two_color": "black",
        "units": "°C",
        "qc_filename": "tmin_tdew"},
    3: {"var_one_name": "Wind Speed",
        "var_one_color": "black",
        "var_two_name": None,
        "var_two_color": None,
        "units": "m/s",
        "qc_filename": "wind"},
    4: {"var_one_name": "Precipitation",
        "var_one_color": "black",
        "var_two_name": None,
        "var_two_color": None,
        "units": "mm",
        "qc_filename": "precip"},
    5: {"var_one_name": "Solar Radiation",
        "var_one_color": "blue",
        "var_two_name": "Clear-Sky Solar Radiation",
        "var_two_color": "black",
        "units": "w/m2",
        "qc_filename": "solar"},
    6: {"var_one_name": "Solar Radiation",
        "var_one_color": "blue",
        "var_two_name": "Thornton-Running Solar Radiation",
        "var_two_color": "black",
        "units": "w/m2",
        "qc_filename": None},
    7: {"var_one_name": "Vapor Pressure",
        "var_one_color": "black",
        "var_two_name": None,
        "var_two_color": None,
        "units": "kPa",
        "qc_filename": "vapor"},
    8: {"var_one_name": "RH Maximum",
        "var_one_color": "blue",
        "var_two_name": "RH Minimum",
        "var_two_color": "red",
        "units": "%",
        "qc_filename": "rhmax_rhmin"},
    9: {"var_one_name": "RH Average",
        "var_one_color": "black",
        "var_two_name": None,
        "var_two_color": None,
        "units": "%",
        "qc_filename": "rhavg"},
    10: {"var_one_name": "Ko Curve",
         "var_one_color": "black",
         "var_two_name": None,
         "var_two_color": None,
         "units": "°C",
         "qc_filename": None}
}


def get_int_input(start_val, end_val, prompt="Enter your choice: "):
    """
        Prompts the user for an integer input within a specified range,
        with handling for if the input is bad or falls outside the expected range.

        Args:
            :start_val: (int) start of acceptable integer values
            :end_val: (int) end of acceptable integer values
            :prompt: (str) prompt to display to the user

        Returns:
            :int_input: (int) sanitized integer value entered by the user
    """

    error_msg = f'Invalid input. Please enter an integer between {start_val} and {end_val}. \n'
    acceptable_vals = np.arange(start_val, end_val+1, step=1, dtype=int)  # add one to end_val, funct excludes stop
    while True:
        try:
            user_input = input(prompt)
            if user_input.isdigit() or user_input[0] in ['+', '-']:  # Check for +/- sign
                # Valid entry, check to see if value is acceptable
                int_input = int(user_input)
                if np.isin(int_input, acceptable_vals):
                    break  # value is acceptable
                else:
                    print(error_msg)
            else:
                print(error_msg)
        except (ValueError, IndexError):
            print(error_msg)
    return int_input


def get_float_input(prompt="Enter your choice: "):
    """
        Prompts the user for a float input, with handling for if the input is bad

        Args:
            :prompt: (str) prompt to display to the user

        Returns:
            :float_input: (float) sanitized value entered by the user
    """

    error_msg = f'Invalid input. Please enter a numerical value.\n'
    while True:
        try:
            user_input = input(prompt)
            if user_input.isnumeric() or user_input[0] in ['+', '-']:  # Check for +/- sign
                float_input = float(user_input)
                break
            else:
                print(error_msg)
        except (ValueError, IndexError):
            print(error_msg)
    return float_input


def validate_file(file_path, expected_extensions):
    """
    Checks to see if provided path is valid, while also checking to see if file is of expected type.
    Raises exceptions if either of those fail. Returns nothing.

    Args:
        :file_path: (str) path to file
        :expected_extensions: (list) possible expected file types
    """
    # Check to see if provided config file path actually points to a file.
    if pl.Path(file_path).is_file():
        # Next check to see if provided file is of the appropriate type.
        # by obtaining the ending suffix and checking it against the expected types
        file_extension = pl.PurePath(file_path).suffix.split('.', 1)[1]  # Remove period
        file_extension = file_extension.lower()  # Make it lowercase

        if file_extension not in expected_extensions:
            raise IOError('\n\nProvided file was of type \'{}\' but script was expecting type \'{}\'.'
                          .format(file_extension, expected_extensions))
        else:
            pass
    else:
        raise IOError('\n\nUnable to find the file at path \'{}\'.'.format(file_path))


def determine_delimiter(file_path):
    """
    Uses the csv.Sniffer class to determine the delimiter of an input file
    Will parse the first 5 lines and raise an error if the delimiter is not consistent

    Args:
        :file_path: (str) path to file to parse
    Returns:
        :delim: (str) delimiter for the input file, to be used in pandas.read_csv()
    """

    print(f'Attempting to parse the input file located at {file_path}.')
    sniffer = csv.Sniffer()
    sniffer.preferred.extend(['|'])  # add to the preferred list of delimiters

    delimiter_list = []
    with open(file_path, 'r') as f:
        for row in range(5):
            line = next(f).strip()
            delim = sniffer.sniff(line).delimiter
            delimiter_list.append(delim)

    # Check to see if file structure is uniform and raise an error if not
    uniform_delimiters = all(i == delimiter_list[0] for i in delimiter_list)
    if not uniform_delimiters:
        raise IOError(f'The file at {file_path} has inconsistent delimiters and cannot be parsed. Delimiters found: \n'
                      f'{delimiter_list}.\n Consider removing the header/footer information if the formatting '
                      f'differs from the rest of the data file.')

    # Uniform delimiters found, return delimiter
    return delim
