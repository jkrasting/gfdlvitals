""" Utiliites for use in averaging routines """

import numpy as np

from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["RichVariable", "generic_cubesphere_driver", "process_var"]


class RichVariable:
    """Metadata-rich variable class

    Parameters
    ----------
    varname : str
        Variable name
    grid_file : io.BufferedReader or list of io.BufferedReader
        Grid-spec tiles
    data_file : io.BufferedReader or list of io.BufferedReader
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
    cell_area : np.ma.masked_array, optional
        Array of cell areas
    area_types : dict, optional
        [description], by default None
    cell_depth : np.ma.masked_array, optional
        [description], by default None
    cell_frac : np.ma.masked_array, optional
        [description], by default None
    soil_area : np.ma.masked_array, optional
        [description], by default None
    soil_frac : np.ma.masked_array, optional
        [description], by default None
    average_dt : np.ma.masked_array
        Array of time averaging period
    """

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
        cell_area=None,
        area_types=None,
        cell_depth=None,
        cell_frac=None,
        soil_area=None,
        soil_frac=None,
        average_dt=None,
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
        self.area_types = area_types
        self.cell_depth = cell_depth
        self.cell_frac = cell_frac
        self.soil_area = soil_area
        self.soil_frac = soil_frac
        self.average_dt = average_dt

    def __str__(self):
        return self.__class__.__name__

    def __hash__(self):
        return hash([self.__dict__[x] for x in list(self.__dict__.keys())])


def process_var(variable, averager=None):
    """Function called by multiprocessing thread to process a variable

    Parameters
    ----------
    variable : RichVariable object
        Input variable to process
    """

    var = None
    _cell_depth = None

    if averager in ["cubesphere", "land_lm4"]:
        # open up data tiles and get variable info
        data_file = [nctools.in_mem_nc(x) for x in variable.data_file]
        varshape = data_file[0].variables[variable.varname].shape
        ndim = len(varshape)
        units = gmeantools.extract_metadata(data_file[0], variable.varname, "units")
        long_name = gmeantools.extract_metadata(
            data_file[0], variable.varname, "long_name"
        )

        if (averager == "land_lm4") and (ndim >= 3):
            cell_measures = gmeantools.extract_metadata(
                data_file[0], variable.varname, "cell_measures"
            )
            area_measure = gmeantools.parse_cell_measures(cell_measures, "area")
            if (area_measure is not None) and (area_measure != "area_ntrl"):
                var = gmeantools.cube_sphere_aggregate(variable.varname, data_file)
                var = np.ma.average(
                    var, axis=0, weights=data_file[0].variables["average_DT"][:]
                )
                _area_weight = variable.area_types[area_measure]
                _cell_depth = variable.cell_depth if ndim == 4 else None

        elif (averager == "cubesphere") and (ndim == 3):
            var = gmeantools.cube_sphere_aggregate(variable.varname, data_file)
            var = np.ma.average(
                var, axis=0, weights=data_file[0].variables["average_DT"][:]
            )
            _area_weight = variable.cell_area

    else:
        fdata = nctools.in_mem_nc(variable.data_file)
        units = gmeantools.extract_metadata(fdata, variable.varname, "units")
        long_name = gmeantools.extract_metadata(fdata, variable.varname, "long_name")
        ndim = len(fdata.variables[variable.varname].shape)

        if (averager == "tripolar") and (ndim >= 3):
            dims = fdata.variables[variable.varname].dimensions
            if (dims[-2::] == ("yh", "xh")) and (ndim == 3):
                var = fdata.variables[variable.varname][:]
            elif (ndim == 4) and (variable.varname[0:9] == "tot_layer"):
                var = fdata.variables[variable.varname][:]
                var = np.ma.sum(var, axis=1).squeeze()
            if var is not None:
                var = np.ma.average(
                    var, axis=0, weights=fdata.variables["average_DT"][:]
                )
                _area_weight = variable.cell_area

        if averager == "ice":
            if ndim == len(variable.cell_area.shape):
                var = fdata.variables[variable.varname][:]

        if averager == "lat-lon" and ndim == 3:
            var = fdata.variables[variable.varname][:]
            var = np.ma.average(var, axis=0, weights=fdata.variables["average_DT"][:])
            _area_weight = variable.cell_area

        if averager == "land-lm3" and ndim >= 3:
            var = fdata[variable.varname][:]
            var = np.ma.average(var, axis=0, weights=fdata["average_DT"][:])

    if var is None:
        return None

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

        if averager == "ice":
            if var.shape != variable.cell_area.shape:
                return None

            # mask by latitude bands
            _v, _area = gmeantools.mask_latitude_bands(
                var, variable.cell_area, variable.geolat, region=reg
            )
            _v = np.ma.sum((_v * _area), axis=(-1, -2)) / np.ma.sum(
                _area, axis=(-1, -2)
            )

            # write out ice annual mean, min, and max
            gmeantools.write_sqlite_data(
                sqlfile, variable.varname + "_max", variable.fyear[:4], np.ma.max(_v)
            )
            gmeantools.write_sqlite_data(
                sqlfile, variable.varname + "_min", variable.fyear[:4], np.ma.min(_v)
            )
            gmeantools.write_sqlite_data(
                sqlfile,
                variable.varname + "_mean",
                variable.fyear[:4],
                np.ma.average(_v, axis=0, weights=variable.average_dt),
            )

            # sum of area not reported for ice diagnostics
            area_sum = None

        # -- Legacy LM3 Land Model
        elif averager == "land-lm3":
            result, summed = gmeantools.legacy_area_mean(
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

            # use the legacy write method of the LM3 version of the land model
            gmeantools.write_sqlite_data(
                sqlfile,
                variable.varname,
                variable.fyear[:4],
                result,
                summed,
                component="land",
            )

            # legacy global mean format did not have land area
            area_sum = None

        else:
            if (averager == "land_lm4") and (_cell_depth is not None):
                if var.shape[0] != _cell_depth.shape[0]:
                    return None

            result, area_sum = gmeantools.area_mean(
                var,
                _area_weight,
                variable.geolat,
                variable.geolon,
                region=reg,
                cell_depth=_cell_depth,
            )

            if (averager == "land_lm4") and (hasattr(result, "mask")):
                return None

            gmeantools.write_sqlite_data(
                sqlfile, variable.varname, variable.fyear[:4], result
            )

        gmeantools.write_metadata(sqlfile, variable.varname, "units", units)
        gmeantools.write_metadata(sqlfile, variable.varname, "long_name", long_name)

        if averager == "land_lm4":
            area_measure = (
                area_measure.replace("area", "volume") if ndim == 4 else area_measure
            )

            gmeantools.write_metadata(
                sqlfile, variable.varname, "cell_measure", area_measure
            )

            gmeantools.write_sqlite_data(
                sqlfile, area_measure, variable.fyear[:4], area_sum
            )

        else:
            if area_sum is not None:
                gmeantools.write_sqlite_data(
                    sqlfile, "area", variable.fyear[:4], area_sum
                )

    if averager in ["cubesphere", "land_lm4"]:
        _ = [x.close() for x in data_file]
    else:
        fdata.close()

    return None


def generic_cubesphere_driver(fyear, tar, modules, average, grid_spec="grid_spec"):
    """Generic cubesphere data driver

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
            extract_from_tar(tar, f"{fyear}.{grid_spec}.tile{x}.nc")
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


def generic_driver(fyear, tar, modules, average, static_file=None):
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

        if static_file is not None:

            assert isinstance(static_file, tuple), "Static file must be a tuple"
            assert (
                len(static_file) == 2
            ), "Static file tuple must have primary and one backup stream"

            staticname = f"{fyear}.{static_file[0]}.nc"
            grid_file = (
                extract_from_tar(tar, staticname)
                if tar_member_exists(tar, staticname)
                else extract_from_tar(tar, f"{fyear}.{static_file[1]}.nc")
            )

        else:
            grid_file = None

        for module in list(modules.keys()):
            fname = f"{fyear}.{module}.nc"
            if tar_member_exists(tar, fname):
                print(f"{fyear} - {module}")
                fdata = extract_from_tar(tar, fname)
                grid_file = fdata if grid_file is None else grid_file
                average(grid_file, fdata, fyear, "./", modules[module])
                del fdata

        del grid_file
