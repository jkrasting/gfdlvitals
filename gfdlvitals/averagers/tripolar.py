""" Utilities for averaging tripolar data """

import multiprocessing

import numpy as np

from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["driver", "process_var", "average"]


def driver(fyear, tar, modules):
    """Run the averager on tripolar ocean history data

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
        staticname = f"{fyear}.ocean_static.nc"
        fgs = (
            extract_from_tar(tar, staticname)
            if tar_member_exists(tar, staticname)
            else extract_from_tar(tar, f"{fyear}.ocean_month.nc")
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
    fdata = nctools.in_mem_nc(variable.fdata)
    units = gmeantools.extract_metadata(fdata, variable.varname, "units")
    long_name = gmeantools.extract_metadata(fdata, variable.varname, "long_name")
    ndims = len(fdata.variables[variable.varname].shape)
    if ndims >= 3:
        if ndims == 3:
            dims = fdata.variables[variable.varname].dimensions
            if dims[-2] == "yh" and dims[-1] == "xh":
                var = fdata.variables[variable.varname][:]
            else:
                return
        elif (ndims == 4) and (variable.varname[0:9] == "tot_layer"):
            var = fdata.variables[variable.varname][:]
            var = np.ma.sum(var, axis=1)
        else:
            return
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


class RichVariable:
    """Metadata-rich variable object"""

    def __init__(
        self,
        varname,
        fgs,
        fdata,
        fyear,
        outdir,
        label,
        geolat,
        geolon,
        cell_area,
    ):
        """Metadata-rich variable object

        Parameters
        ----------
        varname : str
            Variable name
        fgs : bytes object
            Gridspec NetCDF file
        fdata : bytes object
            Input data file
        fyear : str
            Year that is being processed
        outdir : str
            Output path directory
        label : str
            DB file name
        geolat : np.ma.masked_array
            Array of latitudes
        geolon : np.ma.masked_array
            Array of longitudes
        cell_area : np.ma.masked_array
            Array of cell areas
        """
        self.varname = varname
        self.fgs = fgs
        self.fdata = fdata
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

    fgs = nctools.in_mem_nc(grid_file)
    fdata = nctools.in_mem_nc(data_file)

    varlist = list(fgs.variables.keys())

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
        fgs.variables["geolat"][:]
        if "geolat" in varlist
        else fgs.variables["geolat_t"][:]
    )
    geolon = (
        fgs.variables["geolon"][:]
        if "geolon" in varlist
        else fgs.variables["geolon_t"][:]
    )
    cell_area = (
        fgs.variables["areacello"][:]
        if "areacello" in varlist
        else fgs.variables["area_t"][:]
    )

    variables = list(fdata.variables.keys())
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

    fgs.close()
    fdata.close()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var, variables)
