### Data Preparation
This script is run locally from within its directory, so it looks for the configuration file, its modules, and the data file all within its directory. The majority of difficulties you may encounter come from improper configurations with the .ini file or the folder structure.

### Example Run
If you are trying to run this script right after cloning the respository, then you're already configured to run the example data set. You can hop over to the [example run instructions](EXAMPLERUN.md), check it out, and come back here for when you want to configure your own data set.

### Folder Structure
Assuming you have cloned the github directory, your folder should contain the following items:

![](https://i.imgur.com/6jixiub.png)
* The "docs" directory containing the different instruction pages for operation (NOT required for running the script).
* The "qaqc_modules" directory containing the different functions used by the main script.
* config.ini - The configuration file used by the script to find variables in the data file.
* QAQC_Master.py - The actual script you will call to process weather data. Your icon may not match what is pictured here.
* README.md - The readme file for the Github Repository (NOT required for running the script).
* A .csv data file containing the weather data to process. In this example, it is located within the "example_data" folder.

### Setting up your data
First, place your .csv station data file somewhere within the script directory. Next, open up the "config.ini" file.

The QAQC script pulls all relevant parameters from the config.ini file while it is running, which you will fill out prior to running. 

### Configuring the .ini - METADATA
The very top section of the config.ini file is where you will specify the metadata of the data file and of the station to the script.

### Configuring the .ini - MODES
The next section of the config.ini file is where you will specify what modes, or options, you want the script to run with. Examples of this would be whether or not you wanted to correct the data, or whether or not you wanted to plot station-calculated ET.

All of the settings in this section are either set to "0" (indicating FALSE, or NO) or "1" (indicating TRUE, or YES). For most users, the only option you'll actually change will be script_mode, depending on if you want to correct data or not.

### Configuring the .ini - DATA
The majority of work in setting up the config.ini file is in the next section, where we specify what variables are in which columns of data, and what units those variables are in. As an example, we'll look at specifying the details for solar radiation:

The example weather station we are using measures daily cumulative solar radiation (Rs), which we would like to examine, possibly correct, and then use for calculating ET. To do so, we need to specify where in the data file our solar radiation data is. Our data is organized as such:

![](https://i.imgur.com/fD6Qwfb.png)

We can see that Solar radiation data is measured in langleys, and is located in **Column F**, which we would think is the 6th Column. **However, in Python, indexes start at 0**, so Column A would be 0, Column B would be 1, and so on. Accounting for that, we would say **Rs data is actually in Column 5.** 

Now that we have that information, we can go to the relevant section of the .ini file and fill it in:

![](https://i.imgur.com/YKKHPaj.png)

Fill in rs_col with the appropriate value (in this case, 5), and set the appropriate unit flag (in this case, langleys) from "0" (indicating FALSE) to "1" (indicating TRUE).

If, hypothetically, the solar radiation data was provided in w/m2, you would indicate that to the script by having all other unit flags be set to 0 (FALSE). The green box highlights the text that indicates what units are the expected default.

If we look at the section for temperature data:
![](https://i.imgur.com/eUUyG94.png)

We can see that the layout is the same, including the text indicating what the default units are. 

#### Humidity Measurements
Humidity is commonly measured through either:
* Actual Vapor Pressure (Ea)
* Dewpoint Temperature (Tdew)
* Maximum and Minimum Relative Humidity (RHMax and RHMin)
* Average Relative Humidity (RHAvg)

Or some combination of the above, with the top option (Ea) being most desirable, and the bottom option (RHAvg) being the least.

When configuring humidity measurements, input all variables you may have, and the script will automatically pick the most preferable option. The only complexity here is that, should you have both RHMax/RHMin and Ea, you have the option (vappress_rhplot_flag) of plotting RHMax and RHMin in addition to Ea, as the former may make detection of sensor drift in the latter easier. Like all other flags, it must be set to either 0 (FALSE) or 1 (TRUE).

### Running the Script
Once the configuration is done, you are able to run the script and process your data. See either the [readme](../README.md) for instructions on calling the script or the [example run instructions](docs/EXAMPLERUN.md) for a walkthrough of the correction process.
