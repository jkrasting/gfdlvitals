""" Routine for calculating AMOC """

import warnings

try:
    import xoverturning
except:
    warnings.warn("Could not load xoverturning.")
import numpy as np
import xarray as xr
from gfdlvitals.util import gmeantools
from gfdlvitals.util.netcdf import tar_member_exists
from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import in_mem_xr


__all__ = ["mom6_amoc"]


def mom6_amoc(fyear, tar, label="Ocean", outdir="./"):
    """Driver for AMOC calculation in MOM6-class models

    Parameters
    ----------
    fyear : str
        Year label (YYYY)
    tar : tarfile
        In-memory history tarfile object
    label : str
        SQLite output stream name
    outdir : str, path-like
        Path to output SQLite file
    """

    member = f"{fyear}.ocean_annual_z.nc"
    static = f"{fyear}.ocean_static.nc"

    annual_file = (
        extract_from_tar(tar, member, ncfile=True)
        if tar_member_exists(tar, member)
        else None
    )
    static_file = (
        extract_from_tar(tar, static, ncfile=True)
        if tar_member_exists(tar, static)
        else None
    )

    if annual_file is not None and static_file is not None:
        # open the Dataset with the transports
        dset = in_mem_xr(annual_file)

        # select first time level from static file
        # editorial comment: why does the static file have a time dimension?
        dset_static = in_mem_xr(static_file).isel(time=0)

        # merge static DataSet with transport DataSet
        for geo_coord in ["geolon_v", "geolat_v", "wet_v"]:
            if geo_coord in dset_static.variables:
                dset[geo_coord] = xr.DataArray(
                    dset_static[geo_coord].values, dims=dset_static[geo_coord].dims
                )

        required_vars = ["geolon_v", "geolat_v", "umo", "vmo"]
        dset_vars = list(dset.variables)

        if list(set(required_vars) - set(dset_vars)) == []:
            # calculate non-rotated y-ward moc array
            moc = xoverturning.calcmoc(dset, basin="atl-arc", verbose=False)

            # max streamfunction between 20N-80N and 500-2500m depth
            maxsfn = moc.sel(yq=slice(20.0, 80.0), z_i=slice(500.0, 2500.0)).max()
            maxsfn = maxsfn.astype(np.float16).values
            print(f"  AMOC = {maxsfn}")

            # max streamfunction at 26.5N
            rapidsfn = moc.sel(yq=26.5, method="nearest")
            rapidsfn = rapidsfn.sel(z_i=slice(500.0, 2500.0)).max()
            rapidsfn = rapidsfn.astype(np.float16).values
            print(f"  RAPID AMOC = {rapidsfn}")

            # -- Write to sqlite
            gmeantools.write_sqlite_data(
                outdir + "/" + fyear + ".globalAve" + label + ".db",
                "amoc_vh",
                fyear[:4],
                maxsfn,
            )

            gmeantools.write_sqlite_data(
                outdir + "/" + fyear + ".globalAve" + label + ".db",
                "amoc_rapid",
                fyear[:4],
                rapidsfn,
            )

        else:
            warnings.warn(f"{required_vars} are required to calculate AMOC")

    else:
        warnings.warn("AMOC calculation requires ocean_static and ocean_annual_z")
