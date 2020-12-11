Converting SQLite files to NetCDF
=================================

.. code-block:: text

    db2nc [-h] [-o OUTFILE] [-F] [-v] infile

* `infile`: Input file. Format must be sqlite (\*.db)
* `-o, outfile`:  Output file. Default name is out.nc
* `-F, force`:  Clobber existing output file if it exists.
* `-v, verbose`:  Verbose output. Default is quiet output.