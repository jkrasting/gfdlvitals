""" Utilities for averaging tripolar data """

import warnings

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.xrtools as xrtools
import gfdlvitals.util.netcdf as netcdf

__all__ = ["xr_average"]


def xr_average(fyear, tar, modules):
    """xarray-based processing routines for lat-lon model output

    Parameters
    ----------
    fyear : str
        Year being processed (YYYY)
    tar : tarfile
        In-memory tarfile object
    modules : dict
        Mappings of netCDF file names inside the tar file to output db file names
    """

    members = [x for x in modules if netcdf.tar_member_exists(tar, f"{fyear}.{x}.nc")]

    for member in members:
        print(f"{fyear}.{member}.nc")
        data_file = netcdf.extract_from_tar(tar, f"{fyear}.{member}.nc")
        dset = netcdf.in_mem_xr(data_file)

        grid_file = (
            f"{fyear}.ocean_static.nc"
            if netcdf.tar_member_exists(tar, f"{fyear}.ocean_static.nc")
            else f"{fyear}.ocean_month.nc"
        )
        grid_file = netcdf.extract_from_tar(tar, grid_file)
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

        for region in ["global", "nh", "sh", "tropics"]:
            _masked_area = xrtools.xr_mask_by_latitude(
                _area, ds_grid.geolat, region=region
            )
            gmeantools.write_sqlite_data(
                f"{fyear}.{region}Ave{modules[member]}.db",
                "area",
                fyear,
                _masked_area.sum().data,
            )

            weights = dset.average_DT.astype("float") * _masked_area
            _dset_weighted = xrtools.xr_weighted_avg(dset, weights)
            xrtools.xr_to_db(
                _dset_weighted, fyear, f"{fyear}.{region}Ave{modules[member]}.db"
            )
