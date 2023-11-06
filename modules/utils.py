import numpy as np


def get_int_input(start_val, end_val, prompt="Enter your choice: "):
    """
        Prompts the user for an integer input within a specified range,
        with handling for if the input is bad or falls outside the expected range.

        Args:
            start_val (int): start of acceptable integer values
            end_val (int): end of acceptable integer values
            prompt (string): prompt to display to the user

        Returns:
            sanitized integer value entered by the user
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
            prompt (string): prompt to display to the user

        Returns:
            sanitized value entered by the user
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
