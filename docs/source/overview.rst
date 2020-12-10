Overview
========

Scalar diagnostics are important when developing a climate model and when
running multi-decadal to centennial-scale simulations. Scalar diagnostics, 
defined here as global and hemispheric annual means, serve as "vital signs"
of the model. Just as a patient's heart rate, blood pressure, and temperature 
are routinely monitored in the hospital by a doctor to provide important clues 
regarding the patients progress, "vital signs" such air temperature and volume 
mean ocean temperature are fields to monitor when running climate simulations.

Design goals
------------

This package is designed to be as `fast` and as `lightweight` as possible.
Specifically, some desirable features of a package to monitor climate simulations
should:

* be portable across systems from desktop workstations to supercomputers
* not overly depend on third-party packages
* operate on containerized model data output, including tar files
* be multithreaded and take advantage of parallel processing
* provide some limited capability for computing some scalar diagnostics offline

What this package does
----------------------

This package operates on GFDL FMS model output, specifically tar files of NetCDF
output generated during a model simulation.  The package looks for 3-dimensional fields
`(time, latitude, longitude)` across model components and calculates their annual global and
hemispheric means. The data are stored in SQLite format to improve flexibility and 
reliability of the package. Tools are provided to interact natively with the SQLite
files and convert them to other formats.

What this packages does not do
------------------------------

This package makes to assessments about the validity of the model simulation.
No comparisons with observations or reanalyses are performed. The package is not
a general diagnostic framework nor does it provide any further analysis capabilities
such as plotting geographic patterns of the fields or perform any regridding.