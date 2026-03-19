""" Routine for calculating ACC  """

import warnings
import sectionate
import xgcm

import numpy as np
import xarray as xr
from gfdlvitals.util import gmeantools
from gfdlvitals.util.netcdf import tar_member_exists
from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import in_mem_xr

__all__ = ["mom6_acc"]

def mom6_acc(fyear, tar, label="Ocean", outdir="./"):
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
        ds = in_mem_xr(annual_file)
        
        # select first time level from static file
        # editorial comment: why does the static file have a time dimension?
        dss = in_mem_xr(static_file)

        ds = ds[["umo","vmo","z_i"]]
        ds = xr.merge([ds,dss], compat="override", join="outer", combine_attrs="override")
        
        required_vars = ["umo", "vmo", "z_l", "z_i"]
        
        if list(set(required_vars) - set(ds.variables)) == []:

            ds = ds.assign_coords({
                "geolon_c": ds.geolon_c,
                "geolat_c": ds.geolat_c,
                "geolon_v": ds.geolon_v,
                "geolat_v": ds.geolat_v,
                "geolon_u": ds.geolon_u,
                "geolat_u": ds.geolat_u,
            })

            if len(ds["yq"]) > len(ds["yh"]):
                coords = {
                    "X": {"center":"xh", "outer":"xq"},
                    "Y": {"center":"yh", "outer":"yq"},
                }
            else:
                coords = {
                    "X": {"center":"xh", "right":"xq"},
                    "Y": {"center":"yh", "right":"yq"},
                }
            
            grid = xgcm.Grid(
                ds,
                coords=coords,
                boundary={"X":"periodic", "Y":"extend"},
                autoparse_metadata=False
            )
            
            drake_section_lats = [-67.46, -54.76]
            drake_section_lons = [-68.29, -66.32]
            
            i_c, j_c, lons_c, lats_c = sectionate.grid_section(
                grid,
                drake_section_lons,
                drake_section_lats,
                topology="MOM-tripolar"
            )
            
            transport = sectionate.convergent_transport(grid, i_c, j_c)
            
            acc = float(transport.conv_mass_transport.sum()*1.e-9)

            # -- Write to sqlite
            gmeantools.write_sqlite_data(
                outdir + "/" + fyear + ".globalAve" + label + ".db",
                "acc_drake",
                fyear[:4],
                acc,
            )

            print(f"ACC: {acc}")
        
        else:
            warnings.warn(f"{required_vars} are required to calculate ACC")

    else:
        warnings.warn("ACC calculation requires ocean_static and ocean_annual_z")
