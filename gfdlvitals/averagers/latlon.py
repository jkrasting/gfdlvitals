"""Averaging utilities for lat-lon data"""

import multiprocessing

from functools import partial

import numpy as np

from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["average"]


def average(grid_file, data_file, fyear, out, lab):
    """Mid-level averaging routine

    Parameters
    ----------
    grid_file : bytes-like
        Gridspec dataset
    data_file : bytes-like
        Model output dataset
    fyear : str
        Year being processed
    out : str
        Output path directory
    lab : [type]
        DB file name
    """

    _grid_file = nctools.in_mem_nc(grid_file)
    _data_file = nctools.in_mem_nc(data_file)

    lat = _grid_file.variables["lat"][:]
    lon = _grid_file.variables["lon"][:]

    geolat = np.tile(lat[:, None], (1, lon.shape[0]))
    geolon = np.tile(lon[None, :], (lat.shape[0], 1))
    cell_area = gmeantools.standard_grid_cell_area(lat, lon)

    variables = list(_data_file.variables.keys())
    variables = [
        RichVariable(
            x, grid_file, data_file, fyear, out, lab, geolat, geolon, cell_area
        )
        for x in variables
    ]

    _ = [x.close for x in [_grid_file, _data_file]]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "lat-lon"}), variables)
