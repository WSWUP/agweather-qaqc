from bokeh.layouts import gridplot
from bokeh.models import Label, ColumnDataSource, HoverTool
from bokeh.plotting import figure, output_file, reset_output

import numpy as np


def generate_line_plot_features(code, usage=''):
    """
        Generates plot features depending on what code is passed

        Parameters:
            code : integer code passed by main script that indicates what type of data has been passed
            usage : string indicating why this plot is being created, it may be blank.

        Returns:
            units : string of units for passed variable
            title : string for title of plot
            var_one_name : string of first variable name
            var_one_color : string of color code to use for plotting variable one
            var_two_name : string of second variable name
            var_two_color : string of color code to use for plotting variable two
    """

    if code == 1:  # Temperature max and minimum
        var_one_name = 'TMax'
        var_one_color = 'red'
        var_two_name = 'TMin'
        var_two_color = 'blue'
        units = '°C'
        title = usage + var_one_name + ' and ' + var_two_name
    elif code == 2:  # Temperature min and dewpoint
        var_one_name = 'TMin'
        var_one_color = 'blue'
        var_two_name = 'TDew'
        var_two_color = 'black'
        units = '°C'
        title = usage + var_one_name + ' and ' + var_two_name
    elif code == 3:  # Wind Speed
        var_one_name = 'Wind Speed'
        var_one_color = 'black'
        var_two_name = 'null'
        var_two_color = 'black'
        units = 'm/s'
        title = usage + var_one_name
    elif code == 4:  # Precipitation
        var_one_name = 'Precipitation'
        var_one_color = 'black'
        var_two_name = 'null'
        var_two_color = 'black'
        units = 'mm'
        title = usage + var_one_name
    elif code == 5:  # Solar Radiation w/ Rso
        var_one_name = 'Solar Radiation'
        var_one_color = 'blue'
        var_two_name = 'Clear-Sky Solar Radiation'
        var_two_color = 'black'
        units = 'w/m2'
        title = usage + var_one_name + ' and ' + var_two_name
    elif code == 6:  # Solar Radiation w/ Thornton-Running Rs
        var_one_name = 'Solar Radiation'
        var_one_color = 'blue'
        var_two_name = 'Thornton-Running Solar Radiation'
        var_two_color = 'black'
        units = 'w/m2'
        title = usage + var_two_name + ' and ' + var_one_name  # reverse order so titles are clearer
    elif code == 7:  # Humidity - Ea
        var_one_name = 'Vapor Pressure'
        var_one_color = 'black'
        var_two_name = 'null'
        var_two_color = 'black'
        units = 'kPa'
        title = usage + var_one_name
    elif code == 8:  # Humidity - RHMax and RHMin
        var_one_name = 'RHMax'
        var_one_color = 'blue'
        var_two_name = 'RHMin'
        var_two_color = 'red'
        units = '%'
        title = usage + var_one_name + ' and ' + var_two_name
    elif code == 9:  # Humidity - RHAvg
        var_one_name = 'RHAvg'
        var_one_color = 'black'
        var_two_name = 'null'
        var_two_color = 'black'
        units = '%'
        title = usage + var_one_name
    elif code == 10:  # ko curve
        var_one_name = 'ko Curve'
        var_one_color = 'black'
        var_two_name = 'null'
        var_two_color = 'black'
        units = '°C'
        title = usage + var_one_name
    else:
        raise ValueError('Unsupported code type {} passed to generate_line_plot_features.'.format(code))

    if '%' in usage:
        units = '% difference'
    else:
        pass
    return units, title, var_one_name, var_one_color, var_two_name, var_two_color


def histogram_plot(data, title, color, units):
    """
        Creates a histogram and plots it for provided variables against a PDF to see if it is approximately
        normally distributed

        Parameters:
            data : 1D numpy array of original data
            title : string of title for this plot
            color : string of color to use for histogram bars
            units : string of units for x axis

        Returns:
            h_plot : constructed figure with histogram
    """
    mean = np.nanmean(data)
    sigma = np.nanstd(data)

    histogram, edges = np.histogram(data, density=True, bins=100)

    h_plot = figure(title=title, tools='', background_fill_color="#fafafa")
    h_plot.quad(top=histogram, bottom=0, left=edges[:-1], right=edges[1:],
                fill_color=color, line_color="white", alpha=0.5)

    x = np.linspace(float((mean + 3.0 * sigma)), float((mean - 3.0 * sigma)), 1000)
    pdf = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(x - mean) ** 2 / (2 * sigma ** 2))
    h_plot.line(x, pdf, line_color="#ff8888", line_width=4, alpha=0.7, legend_label="PDF")

    h_plot.y_range.start = 0
    h_plot.legend.location = "center_right"
    h_plot.legend.background_fill_color = "#fefefe"
    h_plot.xaxis.axis_label = units
    h_plot.yaxis.axis_label = 'Pr(x)'
    h_plot.grid.grid_line_color = "white"

    return h_plot


def line_plot(x_size, y_size, dt_array, var_one, var_two, code, usage, link_plot=None):
    """
        Creates a bokeh line plot for provided variables and links them if appropriate

        Parameters:
            x_size : x-axis size for plot
            y_size : y-axis size for plot
            dt_array : values for x-axis to label timestep, either daily or mean monthly
            var_one : 1D numpy array of first variable
            var_two : 1D numpy array of second variable
            code : integer indicating what variables were passed
            usage : additional string indicating why plot is being created
            *link_plot : either nothing or the plot we want to link x-axis with

        Returns:
            subplot : constructed figure
    """
    (units, title, var_one_name, var_one_color, var_two_name, var_two_color) = generate_line_plot_features(code, usage)

    date_list = dt_array.tolist()
    source = ColumnDataSource(data=dict(date=date_list, v_one=var_one))
    empty_array = np.zeros(len(date_list))
    empty_array[:] = np.nan

    if var_two is None:
        source.add(empty_array, name='v_two')
    else:
        source.add(var_two, name='v_two')

    tooltips = [
        ('Index', '$index'),
        ('Date', '@date{%F}'),
        ('Value', '$y')]
    formatters = {'@date': 'datetime'}

    if dt_array.size == 12:  # Mean monthly plot
        x_label = 'Month'
        x_axis_type = 'linear'
    else:  # Anything else
        x_label = 'Timestep'
        x_axis_type = 'datetime'

    if link_plot is None:  # No plot to link with
        subplot = figure(
            width=x_size, height=y_size, x_axis_type=x_axis_type,
            x_axis_label=x_label, y_axis_label=units, title=title,
            tools='pan, box_zoom, undo, reset, save')
    else:  # Plot is passed to link x-axis with
        subplot = figure(
            x_range=link_plot.x_range,
            width=x_size, height=y_size, x_axis_type=x_axis_type,
            x_axis_label=x_label, y_axis_label=units, title=title,
            tools='pan, box_zoom, undo, reset, save')

    subplot.line(x='date', y='v_one', line_color=var_one_color, legend_label=var_one_name, source=source)
    if var_two_name.lower() == 'null':
        pass
    else:
        subplot.line(x='date', y='v_two', line_color=var_two_color, legend_label=var_two_name, source=source)

    subplot.legend.location = 'bottom_left'
    subplot.add_tools(HoverTool(tooltips=tooltips, formatters=formatters))

    return subplot


def variable_correction_plots(station, dt_array, var_one, corr_var_one, var_two, corr_var_two, code, folder_path):
    x_size = 800
    y_size = 350
    reset_output()  # clears bokeh output, prevents ballooning file sizes

    delta_var_one = corr_var_one - var_one
    delta_var_two = corr_var_two - var_two

    with np.errstate(divide='ignore', invalid='ignore'):  # Silencing all errors when we divide by a nan
        prct_var_one = ((corr_var_one - var_one) / var_one) * 100.0
        prct_var_two = ((corr_var_two - var_two) / var_two) * 100.0

    # Obtain title based on variables passed for file name
    (units, title, var_one_name, var_one_color, var_two_name, var_two_color) = generate_line_plot_features(code, '')
    output_file(folder_path + "/correction_files/" + station + "_" + title + "_correction_plots.html")

    original_plot = line_plot(x_size, y_size, dt_array, var_one, var_two, code, station + ' Original ', link_plot=None)

    corrected_plot = line_plot(x_size, y_size, dt_array, corr_var_one, corr_var_two, code, 'Corrected ',
                               link_plot=original_plot)

    delta_plot = line_plot(x_size, y_size, dt_array, delta_var_one, delta_var_two, code, 'Deltas of ',
                           link_plot=original_plot)

    percent_plot = line_plot(x_size, y_size, dt_array, prct_var_one, prct_var_two, code, '% Difference of ',
                             link_plot=original_plot)

    corr_fig = gridplot([[original_plot], [corrected_plot], [delta_plot], [percent_plot]],
                        toolbar_location="left", sizing_mode='stretch_both')
    return corr_fig


def humidity_adjustment_plots(station, dt_array, comp_ea, ea, ea_col, tmin, tdew, tdew_col, rhmax, rhmax_col,
                              rhmin, rhmin_col, rhavg, rhavg_col, tdew_ko, folder_path):

    x_size = 800
    y_size = 350
    humidity_plot_list = []
    reset_output()  # clears bokeh output, prevents ballooning file sizes

    output_file(folder_path + "/correction_files/" + station + "_humidity_adjustment_plots.html")

    ea_comp_plot = line_plot(x_size, y_size, dt_array, comp_ea, None, 7, station + ' Composite ', link_plot=None)
    humidity_plot_list.append(ea_comp_plot)

    if ea_col != -1:
        ea_provided_plot = line_plot(x_size, y_size, dt_array, ea, None, 7, 'Provided ', link_plot=ea_comp_plot)
        humidity_plot_list.append(ea_provided_plot)

    if tdew_col != -1:
        tdew_provided_plot = line_plot(x_size, y_size, dt_array, tmin, tdew, 2, 'Provided ', link_plot=ea_comp_plot)
        humidity_plot_list.append(tdew_provided_plot)

    if rhmax_col != -1 and rhmin_col != -1:
        rh_max_min_plot = line_plot(x_size, y_size, dt_array, rhmax, rhmin, 8, '', link_plot=ea_comp_plot)
        humidity_plot_list.append(rh_max_min_plot)

    if rhavg_col != -1:
        rh_avg_plot = line_plot(x_size, y_size, dt_array, rhavg, None, 9, '', link_plot=ea_comp_plot)
        humidity_plot_list.append(rh_avg_plot)

    tdew_ko_filled_plot = line_plot(x_size, y_size, dt_array, tmin, tdew_ko, 2, 'Ko curve ', link_plot=ea_comp_plot)
    humidity_plot_list.append(tdew_ko_filled_plot)

    # Now construct grid plot out of all of the subplots
    number_of_plots = len(humidity_plot_list)
    humid_grid_of_plots = [([None] * 1) for i in range(number_of_plots)]

    for i in range(number_of_plots):
        for j in range(1):
            if len(humidity_plot_list) > 0:
                humid_grid_of_plots[i][j] = humidity_plot_list.pop(0)
            else:
                pass

    humidity_fig = gridplot(humid_grid_of_plots, toolbar_location='left', sizing_mode='stretch_both')

    return humidity_fig


# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
