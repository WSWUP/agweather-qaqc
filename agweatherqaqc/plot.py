from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, output_file, reset_output
from pathlib import Path
import numpy as np

from agweatherqaqc.utils import FEATURES_DICT, BACKGROUND_COLOR


def histogram_plot(data, title, color, units):
    """
        Creates a histogram and plots it for provided variables against a PDF to see if it is approximately
        normally distributed

        Parameters:
            :data: (ndarray) 1D numpy array of original data
            :title: (str) title for this plot
            :color: (str) color to use for histogram bars
            :units: (str) units for the x-axis

        Returns:
            :h_plot: (figure) constructed figure with histogram
    """
    mean = np.nanmean(data)
    sigma = np.nanstd(data)

    histogram, edges = np.histogram(data, density=True, bins=100)

    h_plot = figure(title=title, tools='', background_fill_color=BACKGROUND_COLOR)
    h_plot.quad(top=histogram, bottom=0, left=edges[:-1], right=edges[1:],
                fill_color=color, line_color="white", alpha=0.5)

    x = np.linspace(float((mean + 3.0 * sigma)), float((mean - 3.0 * sigma)), 1000)
    pdf = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(x - mean) ** 2 / (2 * sigma ** 2))
    h_plot.line(x, pdf, line_color="#ff8888", line_width=4, alpha=0.75, legend_label="PDF")

    h_plot.y_range.start = 0
    h_plot.legend.location = "center_right"
    h_plot.legend.background_fill_color = "#fefefe"
    h_plot.xaxis.axis_label = units
    h_plot.yaxis.axis_label = 'Pr(x)'
    h_plot.grid.grid_line_color = "white"

    return h_plot


def line_plot(x_size, y_size, dt_array, var_one, var_two, code, usage, link_plot=None):
    """
        Creates a bokeh line plot for provided variables and links them if appropriate, relies on
        the information stored within utils.FEATURES_DICT to generate correct features for plots

        Parameters:
            :x_size: (int) x-axis size for plot
            :y_size: (int) y-axis size for plot
            :dt_array: (ndarray) values for x-axis to label timestep, either daily or mean monthly
            :var_one: (ndarray) 1D numpy array of first variable
            :var_two: (ndarray)  1D numpy array of second variable
            :code: (int) indicates what variables were passed
            :usage: (str) additional info used in plot title
            :link_plot: (bokeh.figure) either nothing or the plot we want to link x-axis with

        Returns:
            :subplot: (bokeh.figure) constructed figure
    """

    date_list = dt_array.tolist()
    source = ColumnDataSource(data=dict(date=date_list, v_one=var_one))
    empty_array = np.zeros(len(date_list))
    empty_array[:] = np.nan

    if var_two is None:
        source.add(empty_array, name='v_two')
    else:
        source.add(var_two, name='v_two')

    if FEATURES_DICT[code]['var_two_name'] is None:
        title = f'{usage} {FEATURES_DICT[code]["var_one_name"]}'
    else:
        title = f'{usage} {FEATURES_DICT[code]["var_one_name"]} and {FEATURES_DICT[code]["var_two_name"]}'

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
            width=x_size, height=y_size, x_axis_type=x_axis_type, background_fill_color=BACKGROUND_COLOR,
            x_axis_label=x_label, y_axis_label=FEATURES_DICT[code]['units'], title=title,
            tools='pan, box_zoom, undo, reset, save')
    else:  # Plot is passed to link x-axis with
        subplot = figure(
            x_range=link_plot.x_range,
            width=x_size, height=y_size, x_axis_type=x_axis_type, background_fill_color=BACKGROUND_COLOR,
            x_axis_label=x_label, y_axis_label=FEATURES_DICT[code]['units'], title=title,
            tools='pan, box_zoom, undo, reset, save')

    # Plot first variable
    subplot.line(x='date', y='v_one', alpha=0.75, line_width=2, source=source,
                 line_color=FEATURES_DICT[code]['var_one_color'], legend_label=FEATURES_DICT[code]['var_one_name'])

    # Plot second variable if provided
    if FEATURES_DICT[code]['var_two_name'] is not None:
        subplot.line(x='date', y='v_two', alpha=0.75, line_width=2, source=source,
                     line_color=FEATURES_DICT[code]['var_two_color'], legend_label=FEATURES_DICT[code]['var_two_name'])

    # Add legend and tools
    subplot.legend.location = 'bottom_left'
    subplot.add_tools(HoverTool(tooltips=tooltips, formatters=formatters))

    # Format font size
    subplot.title.text_font_size = '12pt'
    subplot.legend.label_text_font_size = '10pt'
    subplot.xaxis.axis_label_text_font_size = '12pt'
    subplot.yaxis.axis_label_text_font_size = '12pt'
    return subplot


def variable_correction_plots(station, dt_array, var_one, corr_var_one, var_two, corr_var_two, code, folder_path):
    """
    Generates a gridplot that showcases how a variable has changes from whatever correction methodology has been applied

    Args:
        :station: (str) name of station used in filenames and titles
        :dt_array: (ndarray) 1-D array of datetime data
        :var_one: (ndarray) 1-D array of variable one data BEFORE correction
        :corr_var_one: (ndarray) 1-D array of variable one data AFTER correction
        :var_two: (ndarray) 1-D array of variable two data BEFORE correction
        :corr_var_two: (ndarray) 1-D array of variable two data AFTER correction
        :code: (int) provides additional information as to what variable is being corrected
        :folder_path: (str) path to output folder to save figures

    Returns:
        :corr_fig: (bokeh.gridplot) final figure of before/after data
    """
    x_size = 800
    y_size = 350
    reset_output()  # clears bokeh output, prevents ballooning file sizes

    delta_var_one = corr_var_one - var_one
    delta_var_two = corr_var_two - var_two

    with np.errstate(divide='ignore', invalid='ignore'):  # Silencing all errors when we divide by a nan
        prct_var_one = ((corr_var_one - var_one) / var_one) * 100.0
        prct_var_two = ((corr_var_two - var_two) / var_two) * 100.0

    # check if output folder exists and create if necessary
    directory_path = f'{folder_path}/correction_files/var_qc_plots/'
    Path(directory_path).mkdir(parents=True, exist_ok=True)
    output_file(f'{directory_path}{station}_{FEATURES_DICT[code]["qc_filename"]}_qc_plots.html')

    original_plot = line_plot(x_size, y_size, dt_array, var_one, var_two, code, f'{station} Original', link_plot=None)

    corrected_plot = line_plot(x_size, y_size, dt_array, corr_var_one, corr_var_two, code, 'Corrected',
                               link_plot=original_plot)

    delta_plot = line_plot(x_size, y_size, dt_array, delta_var_one, delta_var_two, code, 'Δ of',
                           link_plot=original_plot)

    percent_plot = line_plot(x_size, y_size, dt_array, prct_var_one, prct_var_two, code, '% Difference of',
                             link_plot=original_plot)

    corr_fig = gridplot([[original_plot], [corrected_plot], [delta_plot], [percent_plot]],
                        toolbar_location="left", sizing_mode='stretch_both')
    return corr_fig


def humidity_adjustment_plots(station, dt_array, comp_ea, ea, ea_col, tmin, tdew, tdew_col, rhmax, rhmax_col,
                              rhmin, rhmin_col, rhavg, rhavg_col, tdew_ko, folder_path):
    """
    Generates a Bokeh Gridplot for all provided humidity variables to facilitate changing how compiled humidity
    might be calculated from the underlying provided vars.

    See `qaqc_functions.compiled_humidity_adjustment` for more information.

    Args:
        :station: (str) string of station name
        :dt_array: (ndarray) 1D array of datetime data
        :comp_ea: (ndarray) 1D array of vapor pressure compiled from all data sources
        :ea: (ndarray) 1D array of vapor pressure values as provided by input data source, which may be empty
        :ea_col: (int) column of vapor pressure variable in data file, if it is provided
        :tmin: (ndarray) 1D array of minimum temperature values
        :tdew: (ndarray) 1D array of dewpoint temperature values, which may be empty
        :tdew_col: (int) column of Tdew variable in data file, if it is provided
        :rhmax: (ndarray) 1D array of maximum relative humidity values, which may be empty
        :rhmax_col: (int) column of rhmax variable in data file, if it was provided
        :rhmin: (ndarray) 1D array of minimum relative humidity values, which may be empty
        :rhmin_col: (int) column of rhmin variable in data file, if it was provided
        :rhavg: (ndarray) 1D array of average relative humidity values, which may be empty
        :rhavg_col: (int) column of rhavg variable in data file, if it was provided
        :tdew_ko: (ndarray) 1D array of tdew data filled in by tmin-ko curve
        :folder_path: (str) path to output folder for plots

    Returns:
        :humidity_fig: (bokeh.figure) gridplot figure of all humidity variables in the data source

    """
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

    humidity_fig = gridplot(humidity_plot_list, ncols=1, toolbar_location='left', sizing_mode='stretch_both')

    return humidity_fig


# This is never run by itself
if __name__ == "__main__":
    print("\nThis module is called as a part of the QAQC script, it does nothing by itself.")
