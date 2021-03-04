Generating scalar diagnostics for a model experiment
====================================================

The **gfdlvitals** package supports the generation of scalar diagnostics
both embedded within GFDL's modeling working as well as offline via a
command-line interface.

Generating diagnostics through GFDL's FRE workflow
--------------------------------------------------

This is the easiest way to compute the scalar diagnostics. The workflow
is designed to calculate the diagnostics during the `refineDiag` step of the 
workflow that is called immediately before the post-processing, `i.e. frepp`
stage of the workflow.

The ``refineDiag_data_stager_globalAve.csh`` included with the CM4/ESM4-class 
xmls handles this procedure:

.. code-block:: xml

    <!-- sample tag to include in xml file -->
    <refineDiag script="$(NB_ROOT)/mdt_xml/awg_include/refineDiag/refineDiag_data_stager_globalAve.csh"/>

Generating diagnostics offline
------------------------------
This package includes a script called ``gfdlvitals`` that should be present
in your path if the installation was successful.  The usage of the tool is:

.. parsed-literal::
   gfdlvitals [-h] [-o OUTDIR] [-m MODELCLASS] [-c COMPONENT] 
        [-s STARTYEAR] [-e ENDYEAR] [-g GRIDSPEC] HISTORY DIR

* -o, outdir: the directory where the SQLite files are written. Default is current directory
* -m, modelclass: Options include `ESM2`, `CM4`. Default is CM4
* -c, component: Comma-separated list of components to process. Default is all.
* -s, startyear: Starting year to process. Default is all years.
* -e, endyear: Ending year to process. Default is all years.
* -g, gridspec: Path to gridspec tarfile. Used in AMOC calculation. Default is None
* historydir: Path to directory that contains the history tar files from the model

When specifying a component or list of components, available options are 
atmos, ice, land, ocean, obgc, and amoc.

.. note::
   The ``-g`` or ``--gridspec`` option is no longer used. AMOC is generated using the
   ``xoverturtning`` package which relies on grid information contained in the 
   ``ocean_static.nc`` file.  This option is being retained in the driver, however,
   since information in the gridspec file might be used to apply angle corrections 
   to the AMOC transports in the future.

AMOC calculation
----------------
The Atlantic Meridional Overturning Circulation (AMOC) is calculated using `xoverturning`. 
The calculation is available for ocean model version MOM6 or greater. In order to calculate 
AMOC the following variables are required in the ``ocean_annual_z`` output stream:

* umo
* vmo
* geolon
* geolat

Two AMOC scalars are calculated and added to the ``globalAveOcean.db`` file:

1. **amoc_vh**:  The annual mean maximum overturning streamfunction beteween 20-80N and 500-2500m depth. 
2. **amoc_rapid**:  The annual mean maximum overturning streamfunction beteween 25-28N (centered on 26.5N) and 500-2500m depth.

.. note::
   The ``xoverturning`` package has additional options to rotate the transport vectors to true north and to 
   remove the mixed layer thickness flux (``uhml``/``vhml``). Neither of these options are used 
   in ``gfdlvitals``.

   The scalars above are the y-ward meridional overturning (i.e. ``msftyyz``) based on the 
   residual mean freshwater transport, ``vmo``.
