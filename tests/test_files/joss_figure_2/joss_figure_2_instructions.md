Instructions for Recreating Figure 2 in the JOSS Paper
======================================================

1. Call the script (activating the environment if necessary) with the following command: 

    >python qaqc_single_station.py tests/test_files/joss_figure_2/joss_figure_2_config.ini

2. Correcting solar radiation is dependent on the clear-sky solar radiation calculation, which is itself dependent on temperature and humidity observations, so we must correct those variables first.


3. Enter **1** to select temperature maximum and minimum. There are no discrete sections of bad data, so enter **-1** to select all data. Choose option **4** to detect outliers via the modified Z-score approach, and then choose option **1** to be finished.


4. Enter **7** to select relative humidity maximum and minimum. There are no discrete sections of bad data, but there is sensor drift for the period of 2012-2018. Enter **-1** to select all data. Choose option **4** to perform a year-based percentile correction approach, choose **1** as your percentile for correction, and finally choose option **1** to be finished.


5. Enter **5** to select solar radiation. ``agweather-qaqc`` will ask if you want to adjust compiled humidity, however we can skip this step, so enter **0**.


6. After looking at the data, values from the index **3185** to **3211** are suspect and should be removed. Enter those two values to define a correction interval, then choose option **3** to remove the data. After that, chose option **2** to perform another round of corrections.


7. Enter **-1** to select all data, then choose option **4** for a period-based percentile correction. Enter the recommended values of **60** for period length and **6** for the number of points to base your percentile correction off of. Once that is done, enter **1** to be finished with correcting solar radiation data.


8. Enter **0** to be finished with correcting data. ``agweater-qaqc`` will do some final calculations and then exit. The bokeh plot used in Figure 2 will be saved at: 
   >agweather-qaqc\tests\test_files\joss_figure_2\correction_files\var_qc_plots\joss_figure_2_data_solar_qc_plots.html

9. You will have to manipulate the window size and use bokeh's box zoom, pan, and save tools to get an exact match, but the underlying data is the same. The delta values plot was cut from the JOSS paper for the sake of space.