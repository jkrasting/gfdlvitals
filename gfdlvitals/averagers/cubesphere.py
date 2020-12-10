""" Cubesphere averaging utilities """

import multiprocessing

from functools import partial
from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["average"]


def average(grid_file, data_file, fyear, out, lab):
    """Mid-level averaging routine

    Parameters
    ----------
    grid_file : list of bytes
        Gridspec tiles
    data_file : list of bytes
        Data tiles
    fyear : str
        Year being processed
    out : str
        Output path directory
    lab : [type]
        DB file name
    """

    _grid_file = [nctools.in_mem_nc(x) for x in grid_file]

    geolat = gmeantools.cube_sphere_aggregate("grid_latt", _grid_file)
    geolon = gmeantools.cube_sphere_aggregate("grid_lont", _grid_file)
    cell_area = gmeantools.cube_sphere_aggregate("area", _grid_file)

    _ = [x.close() for x in _grid_file]

    variables = list(nctools.in_mem_nc(data_file[0]).variables.keys())
    variables = [
        RichVariable(
            x, grid_file, data_file, fyear, out, lab, geolat, geolon, cell_area
        )
        for x in variables
    ]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "cubesphere"}), variables)
