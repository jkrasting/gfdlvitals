""" Legacy land model averaging routines """

import multiprocessing

from functools import partial

import numpy as np

from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

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

    lat = _data_file["lat"][:]
    lon = _data_file["lon"][:]
    geolon, geolat = np.meshgrid(lon, lat)

    # land areas and fractions
    # global cell_area

    cell_area = _grid_file["land_area"][:]
    cell_frac = _grid_file["land_frac"][:]

    if "soil_area" in _grid_file.variables.keys():
        soil_area = _grid_file["soil_area"][0]
    elif "soil_area" in _data_file.variables.keys():
        soil_area = _data_file["soil_area"][0]
    else:
        raise ValueError("Unable to locate soil area field.")
    soil_frac = np.ma.array(soil_area / (cell_area * cell_frac))

    variables = list(_data_file.variables.keys())
    variables = [
        RichVariable(
            x,
            grid_file,
            data_file,
            fyear,
            out,
            lab,
            geolat,
            geolon,
            cell_area=cell_area,
            cell_frac=cell_frac,
            soil_area=soil_area,
            soil_frac=soil_frac,
        )
        for x in variables
    ]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "land-lm3"}), variables)
