""" Legacy land model averaging routines """

import multiprocessing

import numpy as np

from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists
from gfdlvitals.util.average import RichVariable

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["driver", "process_var", "average"]


def driver(fyear, tar, modules):
    """Run the averager on ice history data

    Parameters
    ----------
    fyear : str
        Year to process (YYYYMMDD)
    tar : tarfile object
        In-memory pointer to history tarfile
    modules : dict
        Dictionary of history nc streams (keys) and output db name (values)
    """
    members = [f"{fyear}.{x}.nc" for x in list(modules.keys())]
    members = [tar_member_exists(tar, x) for x in members]

    if any(members):
        staticname = f"{fyear}.land_static.nc"
        fgs = (
            extract_from_tar(tar, staticname)
            if tar_member_exists(tar, staticname)
            else extract_from_tar(tar, f"{fyear}.land_month.nc")
        )

        for module in list(modules.keys()):
            fname = f"{fyear}.{module}.nc"
            if tar_member_exists(tar, fname):
                print(f"{fyear} - {module}")
                fdata = extract_from_tar(tar, fname)
                average(fgs, fdata, fyear, "./", modules[module])
                del fdata

        del fgs


def process_var(variable):
    """Function called by multiprocessing thread to process a variable

    Parameters
    ----------
    variables : RichVariable object
        Input variable to process
    """
    fdata = nctools.in_mem_nc(variable.data_file)
    varshape = fdata.variables[variable.varname].shape
    if len(varshape) >= 3:
        var = fdata[variable.varname][:]
        var = np.ma.average(var, axis=0, weights=fdata["average_DT"][:])

    if len(varshape) == 3:
        for reg in ["global", "tropics", "nh", "sh"]:
            sqlfile = (
                variable.outdir
                + "/"
                + variable.fyear
                + "."
                + reg
                + "Ave"
                + variable.label
                + ".db"
            )
            avg, summed = gmeantools.legacy_area_mean(
                var,
                variable.cell_area,
                variable.geolat,
                variable.geolon,
                cell_frac=variable.cell_frac,
                soil_frac=variable.soil_frac,
                region=reg,
                varname=variable.varname,
                component="land",
            )
            if not hasattr(avg, "mask"):
                gmeantools.write_sqlite_data(
                    sqlfile,
                    variable.varname,
                    variable.fyear[:4],
                    varmean=avg,
                    varsum=summed,
                    component="land",
                )


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
    pool.map(process_var, variables)
