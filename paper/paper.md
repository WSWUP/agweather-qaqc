---
title: 'agweather-qaqc: An Interactive Python Package for Quality Assurance and Quality Control of Agricultural Weather Data and Calculation of Reference Evapotranspiration'
tags:
  - Python
  - water demand
  - weather station data
  - quality control
authors:
  - name: Christian Dunkerly^[corresponding author]
    orcid: 0000-0003-3592-4118
    affiliation: 1
  - name: Justin Huntington
    affiliation: 1
  - name: Daniel McEvoy
    affiliation: 1, 2
  - name: Richard Allen
    affiliation: 3
affiliations:
  - name: Desert Research Institute
    index: 1
  - name: Western Regional Climate Center
    index: 2
  - name: University of Idaho
    index: 3
date: November 2023
bibliography: paper.bib
---

# Introduction

Agricultural weather stations are one of the key ways to collect necessary observations of field weather conditions for computing reference evapotranspiration (ET~o~), a measure of atmospheric evaporative demand commonly used for determining crop water use, water requirements, and irrigation scheduling [@allen1998]. Common weather station measurements include incoming shortwave solar radiation, air temperature, humidity, wind speed, and precipitation. Accurate, continuous, and consistent measurement of these variables from years to decades is often lacking due to sensor debris, malfunction, drift, poor calibration, limited station maintenance, communication errors, and remote access.  As a result poor quality agricultural weather station data is fairly common, and unless flagged for removal or corrected, will impact the accuracy of any calculation and analysis that uses them [@allen1996]. This is especially important for predictive and intercomparison studies where station data are considered to be ‘truth’ and when comparing to  model predictions and forecasts of weather variables and calculations of ET~o~ [@blankenau2020; @mcevoy2022], or when weather station data are used to validate or to bias-correct  gridded weather and ET~o~ datasets to be more representative of well-watered reference crop conditions [@allen2021; @huntington2018]. More recently, large-scale quality assurance and quality control (QAQC) and use of agricultural weather station data to support satellite remote sensing of agricultural water use, often times collected from dozens of networks and hundreds of stations, is becoming increasingly common and important [@melton2022; @huntington2022]. A common challenge in large-scale weather data compilation and use is developing visualization tools and QAQC workflows to ensure data are reliable and of high quality. Reliable, high-quality records of weather observations will become increasingly important as scarcity in freshwater resources continues to become a more prevalent issue in the world [@gleick2021]. 

# Statement of Need

Having the ability to easily read, visualize, review, flag, and potentially remove, fill, or adjust historical data with efficiency is necessary to advance research and applications focused on evaporative demand and crop water use estimation at local to global scales. The development of the ``agweater-qaqc`` Python package was intended to support the need for efficient weather data review and QAQC. The ``agweater-qaqc`` package  is a command-line interface (CLI) based, open-source Python package for efficiently reading, visualizing, and QAQC of daily weather station observations and calculation of ET~o~. Many applications of weather data require sourcing data from multiple station networks with different storage formats and or recorded variables. For example, humidity might be recorded as vapor pressure, dewpoint temperature, specific humidity, or maximum, minimum, and average relative humidity. Data input variables, units, and conversions are configurable to flexibly handle a wide variety of common input variables and formats so that all input data, visualization, QAQC, and calculation of ET~o~ can be performed in a programmatic, consistent, and easily repeatable manner. Additionally, the CLI-based approach enables researchers and practitioners that are not overly proficient with Python, to easily use and understand the software through the use of helpful reminders, prompts, and recommended settings and parameters. 

One of the most useful utilities of the software is the interactive visualization of weather variable time series for rapid human data assessment and pattern recognition.The observation data is displayed in [Bokeh](https://github.com/bokeh/bokeh) [-@Bokeh] time series plots both before and after the QAQC process, enabling users to easily visualize and assess data patterns and trends related to sensor drift, miscalibration, data outliers, malfunction, etc. These plots are accompanied by interactive tools (ex. pan and zoom controls, display info on hover), and feature linked axis, allowing the user to easily visualize and assess how observations vary and covary over time and at different time scales (e.g. daily, monthly, annual). These graphs are saved as stand-alone HTML files to allow for easy sharing of results.

While ease-of-use for a non-technical user was one of the principle goals, the software workflow can be automated with the inclusion of different libraries such as [PyAutoGUI](https://github.com/asweigart/pyautogui). 

The ``agweater-qaqc`` package features include:

* Importing of daily observational data as is, without having to convert it to a standardized format, with automatic unit conversions based on a user-specified configuration file. 
* Converting multiple input formats from separate sources into a single, uniform source for easier downstream analysis.
* Visualizing data trends both before and after processing with interactive plots, both as daily time series and as mean monthly averages.
* Filtering, both manual and automatic, of data, with statistics-based approaches to correct chronic issues like sensor miscalibration, and manual selection of data to remove suspect observations.
* Calculating grass and alfalfa reference evapotranspiration according to the ASCE-EWRI standardized equation [@asce-ewri2005] via the [RefET](https://github.com/WSWUP/RefET) [@RefET] library.
* Calculating an optimized Thornton-Running solar radiation [@thornton1999] utilizing a Monte-Carlo-based approach calibrated by observed data.
* Optional gap-filling of data using local climatologies, resulting in a complete record of reference evapotranspiration annual totals.
* Creating archival charts and log files that record exactly how each data source was changed during the QAQC process.

The documentation provides more detail on these features, and includes a tutorial with usage examples. An environment.yml is included for installation and third-party package management.

# Design and Features

The ``agweater-qaqc`` package is based on a python class that takes in a data source and standardizes it before allowing the user to QAQC data (\autoref{fig:fig1}).

![Diagram showing the required inputs, flow of data, and produced outputs of the software.\label{fig:fig1}](figure1.pdf)

Inputs to ``agweater-qaqc`` are a tabular data file of daily data, and a configuration file that details where variables are arranged within that file. The configuration file also provides metadata about the station itself, such as latitude and longitude, and what units the variables are in. An optional input of a metadata file for multiple stations may also be provided, enabling a single configuration file to be used for any number of data sources that share a common format. The ``agweater-qaqc`` package contains [example files](https://github.com/WSWUP/pyWeatherQAQC/tree/master/test_files) of each input.

Once given data, the ``AgWeatherQaQc`` class performs both unit conversions and numerical filtering of unreasonable values, such as a negative anemometer reading. This is followed by calculating end-product variables, like grass-reference evapotranspiration, as well as diagnostic variables, like clear-sky theoretical solar radiation (R~so~). CLI prompts facilitate corrections on any variables, and include recommendations as to best practices.  All dependent variables are recalculated once each correction is performed to assemble the best possible version of the data. Once the user is finished making any adjustments, comprehensive output files are generated. ``agweater-qaqc`` tracks all changes through both a human-readable log file, and interactive time series plots of pre- and post-processed observations. The generated output files form a complete record demonstrating exactly how the observation data changed, should archival of the work be important.

There are two optional functionalities enabled by the configuration file: one automates some interactive prompts, the other provides gap-filling of any missing observations to provide for the calculation of complete annual totals of reference evapotranspiration for the period of record.

# Selected Example

Incident shortwave solar radiation (R~s~) data frequently suffers from the pyranometer falling out of calibration (\autoref{fig:fig2}).

![Daily shortwave radiation compared against clear-sky solar radiation.\label{fig:fig2}](figure2.pdf)

``agweater-qaqc`` performs QAQC of R~s~ by comparing it against periodic envelopes of clear-sky solar radiation (R~so~), which is the theoretical maximum daily solar radiation based on a clear sky, day of year, atmospheric water vapor, and global location [@allen1996]. R~s~ should approach R~so~ when a cloud-free day occurs, and potentially surpass it due to incident reflected R~s~ from the environment [@asce-ewri2005]. Observed R~s~ from the winter of 2012 to the summer of 2013 matches this expectation. Observed data after this time features extended periods of R~s~ not approaching R~so~, indicating that the pyranometer has fallen out of calibration, and that observed data should be adjusted to represent observed conditions (\autoref{fig:fig3}).
To perform this adjustment, the data is broken into sixty-day periods. Within each period, a ratio is calculated from the average of the six largest daily R~s~ observations and corresponding R~so~ values. That ratio is then applied to the period to adjust the data. If the ratio of these averages falls between 0.97 and 1.03, no adjustment is applied to prevent overfitting (\autoref{fig:fig4}). The period duration and number of points included in the ratio are both configurable through the interactive prompts.

![Post-QC daily shortwave radiation compared against clear-sky solar radiation.\label{fig:fig3}](figure3.pdf)


![The percent difference between pre- and post-QC values as a result of applying the $\frac{Rso}{Rs}$ ratio to each sixty-day period.\label{fig:fig4}](figure4.pdf)

After the adjustment is performed,  a plot of the cumulative effects of all changes is generated. If these R~s~ observations had not been adjusted, any calculation of reference evapotranspiration from this data would have underrepresented solar radiation by approximately 5-10% for significant stretches of time, falling short of accurately reflecting real water demand. This example highlights how the approaches used and recommended by ``agweater-qaqc`` are representative of the physical processes driving weather data.

Limitations:

* Recommendations are made for what procedures to use, but the end user must ultimately be responsible for the final product.
* Knowledge about the data source being processed is required, such as latitude and the anemometer height.
* If the data source is not located over an irrigated surface, then any generated reference evapotranspiration values will likely be overestimated relative to actual evapotranspiration  [@singh2023].

# State of the Field
``agweater-qaqc`` builds on the concepts and functionality of the Ref-ET Software [@allen2000], which both performs QAQC of data and calculates reference evapotranspiration. ``agweater-qaqc`` makes this functionality open source, and increases accessibility by operating outside the Windows platform. The R package [CrowdQC+](https://github.com/dafenner/CrowdQCplus) and the python library [titanlib](https://github.com/metno/titanlib) both feature statistics-based QAQC of data, however they focus on spatial variation between multiple sources to detect outliers. ``agweater-qaqc`` differs from these libraries by focusing on the temporal variation within a  single source.

# Research enabled by ``agweater-qaqc``
This software was used to generate a CONUS-wide reference dataset of weather stations for ground validation against the gridMET model as part of OpenET [@melton2022], an online water data platform that provides evapotranspiration estimates at the individual field scale across the western United States. This software has also been used to generate a dataset of reference weather stations as part of a yearly Bureau of Reclamation publication on the water demands of the Upper Colorado River Basin [@pearson2019; @pearson2020; @pearson2021], and was used in a skill analysis of the NOAA’s Forecast Reference Evapotranspiration model [@mcevoy2022].

# Acknowledgements

We would like to thank the Bureau of Reclamation and the Western States Water Use Program at the Desert Research Institute for providing the funding for the development of this software. We would also like to thank John Volk, David Ketchum, and Charles Morton for their technical expertise.

# References