Installation
============

.. note::
   This package is not yet avaibable through a package manager (e.g. PyPi or 
   Anaconda). To install, follow the instructions to obtain the source code 
   and install the package manually.

Prerequisites and dependencies
------------------------------

**gfdlvitals** requires Python version 3.6 or greater and several additional pacakages
that are listed below:

* Python >=3.6
* numpy
* netCDF4

Additionally, these packages are required to make plots of the scalar diagnostics
and work with the raw data:
  
* matplotlib
* pandas

Atlantic Meridional Overturning Circulation (AMOC) calculation is available for 
MOM6-class models and requires the following package:

* `xoverturning <https://github.com/raphaeldussin/xoverturning>`_

Obtaining the source code
-------------------------

The primary source for the package code is on GitHub. The ``main`` branch on GitHub 
is a moving development target that is continually tested. To obtain the latest code:

.. parsed-literal::
   git clone https://github.com/jkrasting/gfdlvitals.git

Although the ``main`` branch is suggested for new applications, specific stable releases 
are also tagged and available for download. The `releases <https://github.com/jkrasting/gfdlvitals/releases>`_ 
and their descriptions are tagged on GitHub and can be downloaded:

.. parsed-literal::
   git clone -b <release_name> https://github.com/jkrasting/gfdlvitals.git

Installing the package
----------------------

The package supports installation directly through the included ``setup.py`` script as well 
as through Python's package installer, `pip`.  To install the package in Python's environment for use
by all users:

.. parsed-literal::
   cd gfdlvitals
   pip install .

or:

.. parsed-literal::
   cd gfdlvitals
   python setup.py install

.. Hint::
   If you do not have root access or would prefer not to have a site-wide installation,
   you may install the package in your user's ``~/.local`` directory by passing the ``--user`` 
   flag to the end of either command.

Including in a new conda environment
------------------------------------

If you are building a new conda environment, you can include **gfdlvitals**
in the environment's YAML specification file:

.. code-block:: yaml

   dependencies:
     - python=3.8
     - matplotlib
     - netcdf4
     - numpy
     - pip
     - pip:
       - git+https://github.com/raphaeldussin/xoverturning
       - git+https://github.com/jkrasting/gfdlvitals.git

Appending ``@<release_name>`` at the end of the URL will install a specific
version of the package.

Quick installation
------------------

If you are interested in skipping the download of the source code, you can install 
**gfdlvitals** directly from GitHub into the user ``~/.local`` directory:

.. parsed-literal::
   pip install git+https://github.com/raphaeldussin/xoverturning --user
   pip install git+https://github.com/jkrasting/gfdlvitals.git --user
      