""" Cubesphere averaging utilities """

import multiprocessing

from functools import partial
from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as netcdf

import xarray as xr

__all__ = ["average", "xr_average"]


def xr_average(fyear, tar, modules):
    members = [
        x for x in modules if netcdf.tar_member_exists(tar, f"{fyear}.{x}.tile1.nc")
    ]

    for member in members:
        print(f"{fyear}.{member}.nc")
        data_files = [
            netcdf.extract_from_tar(tar, f"{fyear}.{member}.tile{x}.nc")
            for x in range(1, 7)
        ]
        data_files = [netcdf.in_mem_xr(x) for x in data_files]
        dset = xr.concat(data_files, "tile")

        # Retain only time-dependent variables
        variables = list(dset.variables.keys())
        for x in variables:
            if "time" not in dset[x].dims:
                del dset[x]

        # Aggregate grid spec tiles
        grid_files = [
            netcdf.extract_from_tar(tar, f"{fyear}.grid_spec.tile{x}.nc")
            for x in range(1, 7)
        ]
        grid_files = [netcdf.in_mem_xr(x) for x in grid_files]
        ds_grid = xr.concat(grid_files, "tile")

        dset["area"] = ds_grid["area"]

        for region in ["global", "nh", "sh", "tropics"]:
            _masked_area = gmeantools.xr_mask_by_latitude(dset.area,ds_grid.grid_latt,region=region)
            gmeantools.write_sqlite_data(f"{fyear}.{region}Ave{modules[member]}.db","area",fyear,_masked_area.sum().data)

            weights = dset.average_DT.astype("float") * _masked_area
            _dset_weighted = gmeantools.xr_weighted_avg(dset, weights)
            gmeantools.xr_to_db(
                _dset_weighted, fyear, f"{fyear}.{region}Ave{modules[member]}.db"
            )


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

    _grid_file = [netcdf.in_mem_nc(x) for x in grid_file]

    geolat = gmeantools.cube_sphere_aggregate("grid_latt", _grid_file)
    geolon = gmeantools.cube_sphere_aggregate("grid_lont", _grid_file)
    cell_area = gmeantools.cube_sphere_aggregate("area", _grid_file)

    _ = [x.close() for x in _grid_file]

    variables = list(netcdf.in_mem_nc(data_file[0]).variables.keys())
    variables = [
        RichVariable(
            x, grid_file, data_file, fyear, out, lab, geolat, geolon, cell_area
        )
        for x in variables
    ]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "cubesphere"}), variables)
