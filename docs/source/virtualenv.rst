Installing in a virutal environment
===================================

In some instances, it may make more sense to install **gfdlvitals**
in a virutal environment. This prevents overwriting existing
versions of Python modules that you may have already installed. 
The steps below are for a BASH shell with a system Python installed.

1. Ensure that ``virtualenv`` is installed:

.. code-block:: text

    python3 -m pip install --user virtualenv

2.  Create a virual environment:

.. code-block:: text

    python3 -m venv vitals

3.  Acitvate the virtual environment:

.. code-block:: text

    source vitals/bin/activate

4.  Make sure pip is up-to-date:

.. code-block:: text

    pip install --upgrade pip

5.  Install **gfdlvitals**:

.. code-block:: text

    pip install git+https://github.com/jkrasting/gfdlvitals.git 