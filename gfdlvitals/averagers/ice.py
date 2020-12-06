""" Ice model averaging routines """

import multiprocessing

import numpy as np

from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists

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
        staticname = f"{fyear}.ice_static.nc"
        fgs = (
            extract_from_tar(tar, staticname)
            if tar_member_exists(tar, staticname)
            else extract_from_tar(tar, f"{fyear}.ice_month.nc")
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
    if fdata.variables[variable.varname].shape == variable.cell_area.shape:
        units = gmeantools.extract_metadata(fdata, variable.varname, "units")
        long_name = gmeantools.extract_metadata(fdata, variable.varname, "long_name")
        data = fdata.variables[variable.varname][:]
        for reg in ["global", "nh", "sh"]:
            sqlite_out = (
                variable.outdir
                + "/"
                + variable.fyear
                + "."
                + reg
                + "Ave"
                + variable.label
                + ".db"
            )
            _v, _area = gmeantools.mask_latitude_bands(
                data, variable.cell_area, variable.geolat, region=reg
            )
            _v = np.ma.sum((_v * _area), axis=(-1, -2)) / np.ma.sum(
                _area, axis=(-1, -2)
            )
            gmeantools.write_metadata(sqlite_out, variable.varname, "units", units)
            gmeantools.write_metadata(
                sqlite_out, variable.varname, "long_name", long_name
            )
            gmeantools.write_sqlite_data(
                sqlite_out,
                variable.varname + "_mean",
                variable.fyear[:4],
                np.ma.average(_v, axis=0, weights=variable.average_dt),
            )
            gmeantools.write_sqlite_data(
                sqlite_out, variable.varname + "_max", variable.fyear[:4], np.ma.max(_v)
            )
            gmeantools.write_sqlite_data(
                sqlite_out, variable.varname + "_min", variable.fyear[:4], np.ma.min(_v)
            )
    fdata.close()


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
        average_dt,
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
        average_dt : np.ma.masked_array
            Array of time averaging period
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
        self.average_dt = average_dt

    def __str__(self):
        return self.__class__.__name__

    def __hash__(self):
        return hash([self.__dict__[x] for x in list(self.__dict__.keys())])


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

    fgs = nctools.in_mem_nc(grid_file)
    fdata = nctools.in_mem_nc(data_file)

    geolon = fgs.variables["GEOLON"][:]
    geolat = fgs.variables["GEOLAT"][:]

    average_dt = fdata.variables["average_DT"][:]

    if "CELL_AREA" in fgs.variables.keys():
        earth_radius = 6371.0e3  # Radius of the Earth in 'm'
        cell_area = fgs.variables["CELL_AREA"][:] * (4.0 * np.pi * (earth_radius ** 2))
    elif "area" in fgs.variables.keys():
        cell_area = fgs.variables["area"][:]
    else:
        print("FATAL: unable to determine cell area used in ice model")

    if "siconc" in fdata.variables.keys():
        concentration = fdata.variables["siconc"][:]
    elif "CN" in fdata.variables.keys():
        concentration = np.ma.sum(fdata.variables["CN"][:], axis=-3)
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
            average_dt,
        )
        for x in variables
    ]

    fgs.close()
    fdata.close()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var, variables)
