""" Utilities for working with NetCDF files """

import tarfile
import netCDF4
import xarray as xr

__all__ = ["extract_from_tar", "in_mem_nc", "in_mem_xr", "tar_member_exists"]


def extract_from_tar(tar, member, ncfile=False):
    """Extract individual file from a tar file

    Parameters
    ----------
    tar : either tarfile object or path str
        Path to tar file
    member : str
        Filename to extract from tar file
    ncfile : bool, optional
        Convert to netCDF4.Dataset object, by default False

    Returns
    -------
    in-memory object
        either byte stram or netCDF4.Dataset
    """

    _tar = tarfile.open(tar) if isinstance(tar, str) else tar

    if member not in _tar.getnames():
        member = "./" + member

    data = _tar.extractfile(member)

    if ncfile:
        data = in_mem_nc(data)

    if isinstance(tar, str):
        _tar.close()

    return data


def in_mem_nc(data):
    """Wrapper to convert bytes object to netCDF4.Dataset

    Parameters
    ----------
    data : byte stream object
        In-memory object

    Returns
    -------
    netCDF4.Dataset
        In-memory netCDF4 dataset object
    """

    data = data.read()
    return netCDF4.Dataset("in-mem-file", mode="r", memory=data)


def in_mem_xr(data):
    """Wrapper to convert bytes object to xarray.Dataset

    Parameters
    ----------
    data : byte stream object
        In-memory object

    Returns
    -------
    xarray.Dataset
        In-memory xarray dataset object
    """

    if isinstance(data, netCDF4._netCDF4.Dataset):
        dfile = xr.open_dataset(xr.backends.NetCDF4DataStore(data), use_cftime=True)
    else:
        dfile = xr.open_dataset(data, use_cftime=True)

    return dfile


def tar_member_exists(tar, member):
    """Tests if file exsits inside a tar file

    Parameters
    ----------
    tar : tarfile object
        Opened tarfile handle
    member : str
        Name of file inside tar file

    Returns
    -------
    bool
        True if exists, otherwise False
    """
    if member in tar.getnames():
        status = True
    elif str("./" + member) in tar.getnames():
        status = True
    else:
        status = False

    return status
