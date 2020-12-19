"""Averaging utilities for lat-lon data"""

import multiprocessing

from functools import partial

import numpy as np

from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as netcdf

import xarray as xr

__all__ = ["average", "xr_average"]


def xr_average(fyear, tar, modules):
    members = [x for x in modules if netcdf.tar_member_exists(tar, f"{fyear}.{x}.nc")]

    for member in members:
        print(f"{fyear}.{member}.nc")
        data_file = netcdf.extract_from_tar(tar, f"{fyear}.{member}.nc")
        dset = netcdf.in_mem_xr(data_file)

        geolat = np.tile(dset.lat.data[:, None], (1, dset.lon.data.shape[0]))
        geolon = np.tile(dset.lon.data[None, :], (dset.lat.data.shape[0], 1))

        _geolat = xr.DataArray(geolat, coords=((dset.lat, dset.lon)))
        _geolon = xr.DataArray(geolon, coords=((dset.lat, dset.lon)))
        _area = xr.DataArray(
            gmeantools.standard_grid_cell_area(dset.lat.data, dset.lon.data),
            coords=((dset.lat, dset.lon)),
        )

        # Retain only time-dependent variables
        variables = list(dset.variables.keys())
        for x in variables:
            if "time" not in dset[x].dims:
                del dset[x]

        for region in ["global", "nh", "sh", "tropics"]:
            _masked_area = gmeantools.xr_mask_by_latitude(_area, _geolat, region=region)
            gmeantools.write_sqlite_data(
                f"{fyear}.{region}Ave{modules[member]}.db",
                "area",
                fyear,
                _masked_area.sum().data,
            )

            weights = dset.average_DT.astype("float") * _masked_area
            _dset_weighted = gmeantools.xr_weighted_avg(dset, weights)
            gmeantools.xr_to_db(
                _dset_weighted, fyear, f"{fyear}.{region}Ave{modules[member]}.db"
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

    _grid_file = netcdf.in_mem_nc(grid_file)
    _data_file = netcdf.in_mem_nc(data_file)

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
    pool.map(partial(process_var, **{"averager": "lat-lon"}), variables)
