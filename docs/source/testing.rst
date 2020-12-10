Testing the installation
========================

If you downloaded and installed **gfdlvitals** from the source code, you
can verify the installation using the built-in tests that are driven from
a `Makefile` that is included in the testing directory.

In order to run the tests:

.. parsed-literal::
   cd gfdlvitals/testing
   make check

This command will download a tar file (~277 MB) that contains test model data from 
the pre-industrial control simulations from ESM2 and ESM4. The tests will generate
the scalar diagnostics for each model and compare with reference values that
are stored in the Git repository.

.. note::
   Python-based unit tests are not yet available for this package but are planned 
   for future development.