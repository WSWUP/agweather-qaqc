### Example Run
This document will guide you through running the provided example data set. Provided you have downloaded this by cloning the repository, the config.ini file should be completely setup for you to run it.

**NOTE: Once I've settled on a good example station, I'll update this with screenshots of the correction process.**

Once your data file and config.ini file are setup according to the [data preparation instructions](SETUP.md), follow these steps:

1. Before you correct the data, you should get a good idea of what it looks like. Open the config.ini file, and in the **[MODES]** section, set the flag **script_mode equal to 0**, then run the script. This will read in the data and generate a bokeh plot of all variables prior to correction. The graph and all other outputs will be saved in the same location as the data file.
2. Use that generated graph to get a sense of what variables need to be corrected. Hovering the cursor over a data point will give you its array index, should you need to correct specific sections of data. It may be a good to take some notes during this step.
3. Open the config.ini file again, go back to the **[MODES]** section, set the flag **script_mode equal to 1**, then run the script again. This will cause the script to correct the data.
4. The script will start correcting the data, which it does by prompting you through the terminal window. Follow the prompts to correct the data, which will involve you selecting a variable, correcting it, and then returning to select another, until you're finished.
5. Most corrections can be applied to the full history of data, but if you need to target corrections (such as a single year's Rs data being junk), you can create an interval for just that data. Remember that you can hover over a data point on the bokeh graph to find out what its index is.
6. The recommended order for correcting is TMax+TMin, your humidity variables **(which would be TMin+TDew if you were only given TDew)**, Wind Speed and Precipitation (only if needed), then finally Solar Radiation.
7. Once the corrections are done, exit the script using the prompts to save the data.

The script will generate the following outputs:
* Step 1 will generate a composite graph before corrections: "[filename]_pre_correction_output.html"
* Steps 4+5+6 will generate correction plots for individual variables: "[filename]_[variables]_correction_graph.html"
* Step 7 will generate a composite graph after corrections: "[filename]_complete_corrections_graph.html"
* Step 7 will also generate the corrected output .xlsx data file: "[filename]_output_data.xlsx"
* Step 7 will also generate a log .txt file: "[filename]_corrections_log.txt"
* Another file, "[filename]_data_backup.csv" will also be generated, but it can be ignored or disposed of. It's an echo of the provided data.

### Stuck, Lost, or Confused? Here are some tips:
* **Ultimately, the original data file is never altered, so you're free to experiment with options to see how it affects the data.**
* If you set up a dedicated python environment for the script, are you currently in that environment?
* **If you're experiencing an error that is causing the script to crash,** it is most likely due to an incorrect setup in your data and .ini files. Is there a random "DATA END" string at the end of your file? Are your columns and units properly identified?
* **If you're seeing an error or warning that does NOT cause the script to crash,** you can usually ignore it. It is most often the script warning you that some data is missing.
* If you're confused on what method to use or value to select, each prompt has a recommendation on what to do. Look for either the option marked **(Recommended)** or the value suggested by the prompt for a guide.
* Each time you correct a variable, you're given the option to do another iteration, start over, or exit without saving your corrections, so if you make a mistake you're able to fix it.
* If you come across data that you feel is so bad it's past the point of correction, just select an interval around those values and throw them out. 
* The only correction precipitation or wind speed should ever need is the removal of bad values.
