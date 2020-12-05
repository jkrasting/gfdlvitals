""" Cubesphere averaging utilities """

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
    members = [f"{fyear}.{x}.tile1.nc" for x in list(modules.keys())]
    members = [tar_member_exists(tar, x) for x in members]

    if any(members):
        gs_tiles = [
            extract_from_tar(tar, f"{fyear}.grid_spec.tile{x}.nc") for x in range(1, 7)
        ]

        for module in list(modules.keys()):
            if tar_member_exists(tar, f"{fyear}.{module}.tile1.nc"):
                print(f"{fyear} - {module}")
                data_tiles = [
                    extract_from_tar(tar, f"{fyear}.{module}.tile{x}.nc")
                    for x in range(1, 7)
                ]
                average(gs_tiles, data_tiles, fyear, "./", modules[module])
                del data_tiles

        del gs_tiles


def process_var(variables):
    """Function called by multiprocessing thread to process a variable

    Parameters
    ----------
    variables : RichVariable object
        Input variable to process
    """
    data_tiles = [nctools.in_mem_nc(x) for x in variables.data_tiles]
    units = gmeantools.extract_metadata(data_tiles[0], variables.varname, "units")
    long_name = gmeantools.extract_metadata(
        data_tiles[0], variables.varname, "long_name"
    )
    if len(data_tiles[0].variables[variables.varname].shape) == 3:
        var = gmeantools.cube_sphere_aggregate(variables.varname, data_tiles)
        var = np.ma.average(
            var, axis=0, weights=data_tiles[0].variables["average_DT"][:]
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
    _ = [x.close() for x in data_tiles]


class RichVariable:
    """Metadata-rich variable class"""

    def __init__(
        self,
        varname,
        gs_tiles,
        data_tiles,
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
        gs_tiles : list of bytes
            Grid-spec tiles
        data_tiles : list of bytes
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
        self.gs_tiles = gs_tiles
        self.data_tiles = data_tiles
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


def average(gs_tl, da_tl, fyear, out, lab):
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

    gs_tiles = [nctools.in_mem_nc(x) for x in gs_tl]

    geolat = gmeantools.cube_sphere_aggregate("grid_latt", gs_tiles)
    geolon = gmeantools.cube_sphere_aggregate("grid_lont", gs_tiles)
    cell_area = gmeantools.cube_sphere_aggregate("area", gs_tiles)

    _ = [x.close() for x in gs_tiles]

    variables = list(nctools.in_mem_nc(da_tl[0]).variables.keys())
    variables = [
        RichVariable(x, gs_tl, da_tl, fyear, out, lab, geolat, geolon, cell_area)
        for x in variables
    ]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var, variables)
