""" Ice model averaging routines """

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
    gs_tl : list of bytes
        Gridspec tiles
    da_tl : list of bytes
        Data tiles
    fyear : str
        Year being processed
    out : str
        Output path directory
    lab : [type]
        DB file name
    """

    _grid_file = nctools.in_mem_nc(grid_file)
    _data_file = nctools.in_mem_nc(data_file)

    geolon = _grid_file.variables["GEOLON"][:]
    geolat = _grid_file.variables["GEOLAT"][:]

    average_dt = _data_file.variables["average_DT"][:]

    if "CELL_AREA" in _grid_file.variables.keys():
        earth_radius = 6371.0e3  # Radius of the Earth in 'm'
        cell_area = _grid_file.variables["CELL_AREA"][:] * (
            4.0 * np.pi * (earth_radius ** 2)
        )
    elif "area" in _grid_file.variables.keys():
        cell_area = _grid_file.variables["area"][:]
    else:
        print("FATAL: unable to determine cell area used in ice model")

    if "siconc" in _data_file.variables.keys():
        concentration = _data_file.variables["siconc"][:]
    elif "CN" in _data_file.variables.keys():
        concentration = np.ma.sum(_data_file.variables["CN"][:], axis=-3)
    else:
        print("FATAL: unable to determine ice concentration")

    geolat = np.tile(geolat[None, :], (concentration.shape[0], 1, 1))
    geolon = np.tile(geolon[None, :], (concentration.shape[0], 1, 1))
    cell_area = np.tile(cell_area[None, :], (concentration.shape[0], 1, 1))

    for reg in ["global", "nh", "sh"]:
        sqlite_out = out + "/" + fyear + "." + reg + "Ave" + lab + ".db"
        variables = []
        # area and extent in million square km
        _conc, _area = gmeantools.mask_latitude_bands(
            concentration, cell_area, geolat, region=reg
        )
        variables.append(
            ("area", (np.ma.sum((_conc * _area), axis=(-1, -2)) * 1.0e-12))
        )
        variables.append(
            (
                "extent",
                (
                    np.ma.sum(
                        (np.ma.where(np.greater(_conc, 0.15), _area, 0.0)),
                        axis=(-1, -2),
                    )
                    * 1.0e-12
                ),
            )
        )
        for vname in variables:
            gmeantools.write_sqlite_data(
                sqlite_out,
                vname[0] + "_mean",
                fyear[:4],
                np.ma.average(vname[1], weights=average_dt),
            )
            gmeantools.write_sqlite_data(
                sqlite_out, vname[0] + "_max", fyear[:4], np.ma.max(vname[1])
            )
            gmeantools.write_sqlite_data(
                sqlite_out, vname[0] + "_min", fyear[:4], np.ma.min(vname[1])
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
            average_dt=average_dt,
        )
        for x in variables
    ]

    _grid_file.close()
    _data_file.close()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "ice"}), variables)
