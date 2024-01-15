#########################
Installing agweather-qaqc
#########################

The package agweatherqaqc includes an environment.yml file for easy installation. The file is located at: **"/agweatherqaqc/env/environment.yml"**

The rest of this page is written for a generalist audience.

Anaconda
========
Anaconda is a free and open-source distribution of Python that, in exchange for a larger download, will simplify your setup experience. It also comes pre-installed with the majority of the package requirements for agweather-qaqc.

Visit the `Anaconda website <https://www.anaconda.com/download/>`_ to download the correct Anaconda version (agweather-qaqc requires a version >= 3.9) for your operating system, and then follow the prompts to install it.

Once you're done installing Anaconda, open the Anaconda prompt and type::

    >conda info

You should see some text regarding the version of Anaconda you've installed. If you get an error, you may have made a mistake during the installation.

Setting up the Environment
==========================

Using the Anaconda prompt, navigate to the environment.yml file found at **"/agweatherqaqc/env/environment.yml"**, and then type::

    >conda env create -f environment.yml

And then follow the prompts. This will setup a new environment called **"agweatherqaqc"**, which can be activated by typing::

    >activate agweatherqaqc

After this, setup is complete. Once your `input files are configured <data_preparation.html>`_ agweather-qaqc is ready to run.

.. note::
   You will have to activate your environment whenever you close the Anaconda prompt.

Running the agweather-qaqc
==========================

This package is run locally, so the directory can be placed wherever you want it. See `Data Preparation <data_preparation.html>`_ for more information.

You will run the code by directing the Anaconda prompt to the location of the file **qaqc_single_station.py** and running it from there.

You can get the latest version of agweather-qaqc by cloning its `Github Repository <https://github.com/WSWUP/agweather-qaqc>`_ or by `clicking here. <https://github.com/WSWUP/agweather-qaqc/archive/master.zip>`_





