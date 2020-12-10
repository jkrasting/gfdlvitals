""" Utilities for averaging tripolar data """

import multiprocessing

from functools import partial

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

    varlist = list(_grid_file.variables.keys())

    assert ("geolat" in varlist) or (
        "geolat_t" in varlist
    ), "Unable to determine geolat"
    assert ("geolon" in varlist) or (
        "geolon_t" in varlist
    ), "Unable to determine geolon"
    assert ("areacello" in varlist) or (
        "area_t" in varlist
    ), "Unable to determine ocean cell area"

    geolat = (
        _grid_file.variables["geolat"][:]
        if "geolat" in varlist
        else _grid_file.variables["geolat_t"][:]
    )
    geolon = (
        _grid_file.variables["geolon"][:]
        if "geolon" in varlist
        else _grid_file.variables["geolon_t"][:]
    )
    cell_area = (
        _grid_file.variables["areacello"][:]
        if "areacello" in varlist
        else _grid_file.variables["area_t"][:]
    )

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
            cell_area,
        )
        for x in variables
    ]

    _grid_file.close()
    _data_file.close()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "tripolar"}), variables)
