""" Utilities for averaging tripolar data """

import multiprocessing
import warnings

from functools import partial

from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as netcdf

import xarray as xr
__all__ = ["average", "xr_average"]

def xr_average(fyear, tar, modules):
    members = [
        x for x in modules if netcdf.tar_member_exists(tar, f"{fyear}.{x}.nc")
    ]

    for member in members:
        print(f"{fyear}.{member}.nc")
        data_file = netcdf.extract_from_tar(tar,f"{fyear}.{member}.nc")
        dset = netcdf.in_mem_xr(data_file)

        grid_file = f"{fyear}.ocean_static.nc" if netcdf.tar_member_exists(tar,f"{fyear}.ocean_static.nc") else f"{fyear}.ocean_month.nc"
        grid_file = netcdf.extract_from_tar(tar,grid_file)
        ds_grid = netcdf.in_mem_xr(grid_file)
    
        # Retain only time-dependent variables
        variables = list(dset.variables.keys())
        for x in variables:
            if "time" not in dset[x].dims:
                del dset[x]

        _area = "areacello" if "areacello" in list(ds_grid.variables) else "area_t"
        if "wet" in list(ds_grid.variables):
            _wet = ds_grid["wet"] 
        else:
            _wet = 1.0
            warnings.warn("Unable to find wet mask")
        _area = ds_grid[_area] * _wet
            
        for region in ['global','nh','sh','tropics']:
            _masked_area = gmeantools.xr_mask_by_latitude(_area,ds_grid.geolat,region=region)
            gmeantools.write_sqlite_data(f"{fyear}.{region}Ave{modules[member]}.db","area",fyear,_masked_area.sum().data)

            weights = dset.average_DT.astype("float") * _masked_area
            _dset_weighted = gmeantools.xr_weighted_avg(dset,weights)
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

    varlist = list(_grid_file.variables.keys())

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
        _grid_file.variables["geolat"][:]
        if "geolat" in varlist
        else _grid_file.variables["geolat_t"][:]
    )
    geolon = (
        _grid_file.variables["geolon"][:]
        if "geolon" in varlist
        else _grid_file.variables["geolon_t"][:]
    )
    cell_area = (
        _grid_file.variables["areacello"][:]
        if "areacello" in varlist
        else _grid_file.variables["area_t"][:]
    )

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
            cell_area,
        )
        for x in variables
    ]

    _grid_file.close()
    _data_file.close()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "tripolar"}), variables)
