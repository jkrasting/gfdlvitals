"""Land LM4.1 Averaging Routines"""

import multiprocessing
import re

import numpy as np

from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists
from gfdlvitals.util.average import RichVariable

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["driver", "process_var", "average"]


def driver(fyear, tar, modules):
    """Run the averager on LM4 land history data

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
            extract_from_tar(tar, f"{fyear}.land_static.tile{x}.nc")
            for x in range(1, 7)
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


def process_var(variable):
    """Function called by multiprocessing thread to process a variable

    Parameters
    ----------
    variables : RichVariable object
        Input variable to process
    """
    data_tiles = [nctools.in_mem_nc(x) for x in variable.data_tiles]

    varshape = data_tiles[0].variables[variable.varname].shape
    units = gmeantools.extract_metadata(data_tiles[0], variable.varname, "units")
    long_name = gmeantools.extract_metadata(
        data_tiles[0], variable.varname, "long_name"
    )
    cell_measures = gmeantools.extract_metadata(
        data_tiles[0], variable.varname, "cell_measures"
    )
    area_measure = gmeantools.parse_cell_measures(cell_measures, "area")
    if (area_measure is not None) and (area_measure != "area_ntrl"):
        if len(varshape) >= 3:
            var = gmeantools.cube_sphere_aggregate(variable.varname, data_tiles)
            var = np.ma.average(
                var, axis=0, weights=data_tiles[0].variables["average_DT"][:]
            )

            if len(varshape) == 3:
                for reg in ["global", "tropics", "nh", "sh"]:
                    result, area_sum = gmeantools.area_mean(
                        var,
                        variable.area_types[area_measure],
                        variable.geolat,
                        variable.geolon,
                        region=reg,
                    )
                    if not hasattr(result, "mask"):
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
                        gmeantools.write_metadata(
                            sqlfile, variable.varname, "units", units
                        )
                        gmeantools.write_metadata(
                            sqlfile, variable.varname, "long_name", long_name
                        )
                        gmeantools.write_metadata(
                            sqlfile, variable.varname, "cell_measure", area_measure
                        )
                        gmeantools.write_sqlite_data(
                            sqlfile, variable.varname, variable.fyear[:4], result
                        )
                        gmeantools.write_sqlite_data(
                            sqlfile, area_measure, variable.fyear[:4], area_sum
                        )

            elif len(varshape) == 4:
                if varshape[1] == variable.cell_depth.shape[0]:
                    for reg in ["global", "tropics", "nh", "sh"]:
                        result, vol_sum = gmeantools.area_mean(
                            var,
                            variable.area_types[area_measure],
                            variable.geolat,
                            variable.geolon,
                            region=reg,
                            cell_depth=variable.cell_depth,
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
                        gmeantools.write_metadata(
                            sqlfile, variable.varname, "units", units
                        )
                        gmeantools.write_metadata(
                            sqlfile, variable.varname, "long_name", long_name
                        )
                        gmeantools.write_metadata(
                            sqlfile,
                            variable.varname,
                            "cell_measure",
                            area_measure.replace("area", "volume"),
                        )
                        gmeantools.write_sqlite_data(
                            sqlfile, variable.varname, variable.fyear[:4], result
                        )
                        gmeantools.write_sqlite_data(
                            sqlfile,
                            area_measure.replace("area", "volume"),
                            variable.fyear[:4],
                            vol_sum,
                        )


class RichVariable:
    """Metadata-rich variable object"""

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
        area_types,
        cell_depth,
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
        """
        self.varname = varname
        self.gs_tiles = gs_tiles
        self.data_tiles = data_tiles
        self.fyear = fyear
        self.outdir = outdir
        self.label = label
        self.geolat = geolat
        self.geolon = geolon
        self.area_types = area_types
        self.cell_depth = cell_depth

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
    _data_file = [nctools.in_mem_nc(x) for x in data_file]

    for land_file in [_data_file, _grid_file]:
        if "geolat_t" in land_file[0].variables:
            geolat = gmeantools.cube_sphere_aggregate("geolat_t", _data_file)
            geolon = gmeantools.cube_sphere_aggregate("geolon_t", _data_file)
            break

    area_types = {}
    for land_file in [_data_file, _grid_file]:
        for variable in sorted(land_file[0].variables):
            if re.match(r".*_area", variable) or re.match(r"area.*", variable):
                # for now, skip the area variables that depend on time
                timedependent = False
                for dimension in land_file[0].variables[variable].dimensions:
                    timedependent = (
                        timedependent
                        or land_file[0].dimensions[dimension].isunlimited()
                    )
                if not timedependent:
                    if variable not in area_types.keys():
                        area_types[variable] = gmeantools.cube_sphere_aggregate(
                            variable, land_file
                        )

    depth = _data_file[0].variables["zhalf_soil"][:]
    cell_depth = []
    for i in range(1, len(depth)):
        thickness = round((depth[i] - depth[i - 1]), 2)
        cell_depth.append(thickness)
    cell_depth = np.array(cell_depth)

    variables = list(_data_file[0].variables.keys())
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
            area_types=area_types,
            cell_depth=cell_depth,
        )
        for x in variables
    ]

    _ = [x.close() for x in _grid_file]
    _ = [x.close() for x in _data_file]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var, variables)
