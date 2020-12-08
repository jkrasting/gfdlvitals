""" Cubesphere averaging utilities """

import multiprocessing

import numpy as np

from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.average import RichVariable
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
    members = [f"{fyear}.{x}.tile1.nc" for x in list(modules.keys())]
    members = [tar_member_exists(tar, x) for x in members]

    if any(members):
        grid_file = [
            extract_from_tar(tar, f"{fyear}.grid_spec.tile{x}.nc") for x in range(1, 7)
        ]

        for module in list(modules.keys()):
            if tar_member_exists(tar, f"{fyear}.{module}.tile1.nc"):
                print(f"{fyear} - {module}")
                data_file = [
                    extract_from_tar(tar, f"{fyear}.{module}.tile{x}.nc")
                    for x in range(1, 7)
                ]
                average(grid_file, data_file, fyear, "./", modules[module])
                del data_file

        del grid_file


def process_var(variables):
    """Function called by multiprocessing thread to process a variable

    Parameters
    ----------
    variables : RichVariable object
        Input variable to process
    """
    data_file = [nctools.in_mem_nc(x) for x in variables.data_file]
    units = gmeantools.extract_metadata(data_file[0], variables.varname, "units")
    long_name = gmeantools.extract_metadata(
        data_file[0], variables.varname, "long_name"
    )
    if len(data_file[0].variables[variables.varname].shape) == 3:
        var = gmeantools.cube_sphere_aggregate(variables.varname, data_file)
        var = np.ma.average(
            var, axis=0, weights=data_file[0].variables["average_DT"][:]
        )
        for reg in ["global", "tropics", "nh", "sh"]:
            result, area_sum = gmeantools.area_mean(
                var, variables.cell_area, variables.geolat, variables.geolon, region=reg
            )
            sqlfile = (
                variables.outdir
                + "/"
                + variables.fyear
                + "."
                + reg
                + "Ave"
                + variables.label
                + ".db"
            )
            gmeantools.write_metadata(sqlfile, variables.varname, "units", units)
            gmeantools.write_metadata(
                sqlfile, variables.varname, "long_name", long_name
            )
            gmeantools.write_sqlite_data(
                sqlfile, variables.varname, variables.fyear[:4], result
            )
            gmeantools.write_sqlite_data(sqlfile, "area", variables.fyear[:4], area_sum)
    _ = [x.close() for x in data_file]


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
        """Metadata-rich variable object

        Parameters
        ----------
        varname : str
            Variable name
        grid_file : list of bytes
            Grid-spec tiles
        data_file : list of bytes
            Data tiles
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
    pool.map(process_var, variables)
