""" Cubesphere averaging utilities """

import xarray as xr

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.xrtools as xrtools
import gfdlvitals.util.netcdf as netcdf

__all__ = ["xr_average"]


def xr_average(fyear, tar, modules):
    """xarray-based processing routines for cubed sphere atmos. output

    Parameters
    ----------
    fyear : str
        Year being processed (YYYY)
    tar : tarfile
        In-memory tarfile object
    modules : dict
        Mappings of netCDF file names inside the tar file to output db file names
    """

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
            _masked_area = xrtools.xr_mask_by_latitude(
                dset.area, ds_grid.grid_latt, region=region
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
