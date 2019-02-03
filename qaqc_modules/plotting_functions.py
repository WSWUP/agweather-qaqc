from bokeh.plotting import figure, output_file, reset_output, save


def create_plot(x_size, y_size, dt_array, var_one, var_one_text, var_one_color, var_two, var_two_text, var_two_color,
                units, link_plot=None):
    """
        Creates a bokeh plot for provided variables and links them if appropriate

        Parameters:
            x_size : x-axis size for plot
            y_size : y-axis size for plot
            dt_array : values for x-axis to label timestep, either daily or mean monthly
            var_one : 1D numpy array of first variable
            var_one_text : string of var_one name
            var_one_color : color to be used in plotting var_one
            var_two : 1D numpy array of second variable
            var_two_text : string of var_two name
            var_two_color : color to be used in plotting var_two
            units : string of units on y-axis
            *link_plot : either nothing or the plot we want to link x-axis with

        Returns:
            subplot : constructed figure
    """
    # Create title based on variables passed
    if var_two_text.lower() == 'null':
        subplot_title = var_one_text
    else:
        subplot_title = var_one_text + ' and ' + var_two_text

    if dt_array.size == 12:  # Mean monthly plot
        x_label = 'Month'
        x_axis_type = 'linear'
    else:  # Anything else
        x_label = 'Timestep'
        x_axis_type = 'datetime'

    if link_plot is None:  # No plot to link with
        subplot = figure(
            width=x_size, height=y_size, x_axis_type=x_axis_type,
            x_axis_label=x_label, y_axis_label=units, title=subplot_title,
            tools='pan, box_zoom, undo, reset, hover, save')
    else:  # Plot is passed to link x-axis with
        subplot = figure(
            x_range=link_plot.x_range,
            width=x_size, height=y_size, x_axis_type=x_axis_type,
            x_axis_label=x_label, y_axis_label=units, title=subplot_title,
            tools='pan, box_zoom, undo, reset, hover, save')

    subplot.line(dt_array, var_one, line_color=var_one_color, legend=var_one_text)
    if var_two_text.lower() == 'null':
        pass
    else:
        subplot.line(dt_array, var_two, line_color=var_two_color, legend=var_two_text)

    subplot.legend.location = 'bottom_left'

    return subplot
