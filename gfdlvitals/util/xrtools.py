""" Tools for working with xarray datasets """

import xarray as xr

from gfdlvitals.util.gmeantools import write_sqlite_data
from gfdlvitals.util.gmeantools import write_metadata

__all__ = ["xr_mask_by_latitude", "xr_to_db", "xr_weighted_avg"]


def xr_mask_by_latitude(arr, geolat, region=None):
    """Masks an xarray object based on a latitude range

    Parameters
    ----------
    arr : xarray.DataArray or xarray.DataSet
        Input unmasked object
    geolat : xarray.DataArray
        Data Array of latitude coordinates
    region : str, optional
        Predefined region of "global","nh","sh","tropics", by default None

    Returns
    -------
    Masked xarray data object
    """

    arr = arr.copy()

    if region == "nh":
        result = arr.where(geolat > 30.0, 0.0)
    elif region == "sh":
        result = arr.where(geolat < -30.0, 0.0)
    elif region == "tropics":
        result = arr.where((geolat >= -30.0) & (geolat <= 30.0), 0.0)
    else:
        result = arr

    return result


def xr_to_db(dset, fyear, sqlfile):
    """Writes Xarray dataset to SQLite format

    Parameters
    ----------
    dset : xarray.DataSet
        Input dataset
    fyear : str
        Year label (YYYY)
    sqlfile : str
        Filename of output db file
    """
    for var in list(dset.variables):
        write_sqlite_data(sqlfile, var, str(fyear), str(dset[var].data))
        if "units" in list(dset[var].attrs):
            write_metadata(sqlfile, var, "units", dset[var].units)
        if "long_name" in list(dset[var].attrs):
            write_metadata(sqlfile, var, "long_name", dset[var].long_name)
        if "measure" in list(dset[var].attrs):
            write_metadata(sqlfile, var, "cell_measure", dset[var].measure)


def xr_weighted_avg(dset, weights):
    """Generates weighted space and time average of an xarray DataSet

    Parameters
    ----------
    dset : xarray.DataSet
        Input dataset
    weights : xarray.DataArray or list
        Array to use for weights

    Returns
    -------
    xarray DataSet containing weighted averages
    """
    _weights = [weights] if not isinstance(weights, list) else weights

    _dset = xr.Dataset()
    result = xr.Dataset()

    for weight in _weights:
        variables = list(dset.variables.keys())
        for x in variables:
            if sorted(dset[x].dims) == sorted(weight.dims):
                _dset[x] = dset[x]

        _dset_weighted = _dset.weighted(weight).mean()
        for x in list(_dset_weighted.variables):
            _dset_weighted[x] = _dset_weighted[x].astype(dset[x].dtype)
            _dset_weighted[x].attrs = dset[x].attrs

        result = result.merge(_dset_weighted)

    return result
