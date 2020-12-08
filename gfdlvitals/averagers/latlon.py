"""Averaging utilities for lat-lon data"""

import multiprocessing

import numpy as np

from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["driver", "process_var", "average"]


def driver(fyear, tar, modules):
    """Run the averager on cubesphere history data

    Parameters
    ----------
    fyear : str
        Year to process (YYYYMMDD)
    tar : tarfile object
        In-memory pointer to history tarfile
    modules : dict
        Dictionary of history nc streams (keys) and output db name (values)
    """

    for module in list(modules.keys()):
        if tar_member_exists(tar, f"{fyear}.{module}.nc"):
            grid_file = extract_from_tar(tar, f"{fyear}.{module}.nc")
            if tar_member_exists(tar, f"{fyear}.{module}.nc"):
                print(f"{fyear} - {module}")
                data_file = extract_from_tar(tar, f"{fyear}.{module}.nc")
                average(grid_file, data_file, fyear, "./", modules[module])
                del data_file
            del grid_file


def process_var(variable):
    """Function called by multiprocessing thread to process a variable

    Parameters
    ----------
    variables : RichVariable object
        Input variable to process
    """
    fdata = nctools.in_mem_nc(variable.data_file)
    units = gmeantools.extract_metadata(fdata, variable.varname, "units")
    long_name = gmeantools.extract_metadata(fdata, variable.varname, "long_name")
    if len(fdata.variables[variable.varname].shape) == 3:
        var = fdata.variables[variable.varname][:]
        var = np.ma.average(var, axis=0, weights=fdata.variables["average_DT"][:])
        for reg in ["global", "tropics", "nh", "sh"]:
            result, area_sum = gmeantools.area_mean(
                var, variable.cell_area, variable.geolat, variable.geolon, region=reg
            )
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
            gmeantools.write_metadata(sqlfile, variable.varname, "units", units)
            gmeantools.write_metadata(sqlfile, variable.varname, "long_name", long_name)
            gmeantools.write_sqlite_data(
                sqlfile, variable.varname, variable.fyear[:4], result
            )
            gmeantools.write_sqlite_data(sqlfile, "area", variable.fyear[:4], area_sum)
    fdata.close()


class RichVariable:
    """Metadata-rich variable class"""

    def __init__(
        self,
        varname,
        grid_file,
        data_file,
        fyear,
        outdir,
        label,
        geolat,
        geolon,
        cell_area,
    ):
        self.varname = varname
        self.grid_file = grid_file
        self.data_file = data_file
        self.fyear = fyear
        self.outdir = outdir
        self.label = label
        self.geolat = geolat
        self.geolon = geolon
        self.cell_area = cell_area

    def __str__(self):
        return self.__class__.__name__

    def __hash__(self):
        return hash([self.__dict__[x] for x in list(self.__dict__.keys())])


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
    pool.map(process_var, variables)
