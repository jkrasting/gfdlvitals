"""Averaging utilities for lat-lon data"""


import numpy as np
import xarray as xr

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
            _masked_area = xrtools.xr_mask_by_latitude(_area, _geolat, region=region)
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
