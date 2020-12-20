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
   gfdlvitals [-h] [-o OUTDIR] [-m MODELCLASS] [-s STARTYEAR] 
        [-e ENDYEAR] [-g GRIDSPEC] HISTORY DIR

* -o, outdir: the directory where the SQLite files are written. Default is current directory
* -m, modelclass: Options include `ESM2`, `CM4`. Default is CM4
* -s, startyear: Starting year to process. Default is all years.
* -e, endyear: Ending year to process. Default is all years.
* -g, gridspec: Path to gridspec tarfile. Used in AMOC calculation. Default is None
* historydir: Path to directory that contains the history tar files from the model

.. note::
   The ``-g`` or ``--gridspec`` option is only required if you wish to calculate
   the magnitude of the Atlantic Meridional Overturning Circulation (AMOC) strength.
   This feature is not available for the ESM2-class models.
