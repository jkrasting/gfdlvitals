import os
import tarfile

import numpy as np

import xarray as xr

import gfdlvitals as gv

from gfdlvitals import averagers
from gfdlvitals import diags
from gfdlvitals.util import extract_ocean_scalar
from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists

from gfdlvitals.util.average import generic_cubesphere_driver
from gfdlvitals.util.average import generic_driver

import gfdlvitals.util.netcdf as nctools

__all__ = ["routines"]

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as netcdf



def routines(args, infile):

    # -- Open the tarfile
    tar = tarfile.open(infile)
    members = tar.getnames()

    # -- Set the model year string
    fyear = str(infile.split("/")[-1].split(".")[0])
    print("Processing " + fyear)

    # -- Atmospheric Fields
    modules = {
        "atmos_month": "Atmos",
        "atmos_co2_month": "Atmos",
        "atmos_month_aer": "AtmosAer",
        "aerosol_month_cmip": "AeroCMIP",
    }
    averagers.cubesphere.xr_average(fyear, tar, modules)

    # -- Land Fields
    modules = {"land_month": "Land"}
    averagers.land_lm4.xr_average(fyear, tar, modules)

    # # -- Ice
    # modules = {"ice_month": "Ice"}
    # generic_driver(
    #     fYear,
    #     tar,
    #     modules,
    #     averagers.ice.average,
    #     static_file=("ice_static", "ice_month"),
    # )

    ## ## data_file = netcdf.extract_from_tar(tar,f"{fyear}.ice_month.nc")
    ## ## dset = netcdf.in_mem_xr(data_file)
    
    ## ## grid_file = netcdf.extract_from_tar(tar,f"{fyear}.ice_static.nc")
    ## ## ds_grid = netcdf.in_mem_xr(grid_file)
    
    ## ## # Retain only time-dependent variables
    ## ## variables = list(dset.variables.keys())
    ## ## for x in variables:
    ## ##     if "time" not in dset[x].dims:
    ## ##         del dset[x]
    
    ## ## earth_radius = 6371.0e3  # Radius of the Earth in 'm'
    ## ## _area = ds_grid["CELL_AREA"] * 4.0 * np.pi * (earth_radius ** 2)
    
    ## ## #--- todo Add in concentration and extent
    
    ## ## global_weights = dset.average_DT.astype("float") * _area
    
    ## ## for region in ['global','nh','sh']:
    ## ##         weights = xr_mask_weights(global_weights,ds_grid.GEOLAT,region=region)
    ## ##         _dset_weighted = xr_weighted_avg(dset,global_weights)
    ## ##         xr_to_db(_dset_weighted,f"{fyear}.{region}AveIce.db")
    

    # # -- Ocean
    # fname = f"{fYear}.ocean_scalar_annual.nc"
    # if tar_member_exists(tar, fname):
    #     print(f"{fYear} - ocean_scalar_annual")
    #     fdata = nctools.extract_from_tar(tar, fname, ncfile=True)
    #     extract_ocean_scalar.mom6(fdata, fYear, "./")
    #     fdata.close()

    # # -- OBGC
    # modules = {
    #     "ocean_cobalt_sfc": "OBGC",
    #     "ocean_cobalt_misc": "OBGC",
    #     "ocean_cobalt_tracers_year": "OBGC",
    #     "ocean_cobalt_tracers_int": "OBGC",
    #     "ocean_bling": "OBGC",
    #     "ocean_bling_cmip6_omip_2d": "OBGC",
    #     "ocean_bling_cmip6_omip_rates_year_z": "OBGC",
    #     "ocean_bling_cmip6_omip_sfc": "OBGC",
    #     "ocean_bling_cmip6_omip_tracers_month_z": "OBGC",
    #     "ocean_bling_cmip6_omip_tracers_year_z": "OBGC",
    # }
    # generic_driver(
    #     fYear,
    #     tar,
    #     modules,
    #     averagers.tripolar.average,
    #     static_file=("ocean_static", "ocean_month"),
    # )

    ## ## data_file = netcdf.extract_from_tar(tar,f"{fyear}.ocean_bling_cmip6_omip_sfc.nc")
    ## ## dset = netcdf.in_mem_xr(data_file)
    
    ## ## grid_file = netcdf.extract_from_tar(tar,f"{fyear}.ocean_static.nc")
    ## ## ds_grid = netcdf.in_mem_xr(grid_file)
    
    ## ## # Retain only time-dependent variables
    ## ## variables = list(dset.variables.keys())
    ## ## for x in variables:
    ## ##     if "time" not in dset[x].dims:
    ## ##         del dset[x]
    ## ##         
    ## ## _area = ds_grid["areacello"]
    ## ##     
    ## ## areasum = _area.sum()
    ## ## global_weights = dset.average_DT.astype("float") * _area

    ## ## for region in ['global','nh','sh','tropics']:
    ## ##     weights = xr_mask_weights(global_weights,ds_grid.geolat,region=region)
    ## ##     _dset_weighted = xr_weighted_avg(dset,global_weights)
    ## ##     xr_to_db(_dset_weighted,f"{fyear}.{region}AveOBGC.db")

    # # -- AMOC
    # if args.gridspec is not None:
    #     gs_tar = tarfile.open(args.gridspec)
    #     ocean_hgrid = extract_from_tar(gs_tar, "ocean_hgrid.nc", ncfile=True)
    #     topog = extract_from_tar(gs_tar, "ocean_topog.nc", ncfile=True)
    #     fname = f"{fYear}.ocean_annual_z.nc"
    #     if tar_member_exists(tar, fname):
    #         vhFile = extract_from_tar(tar, fname, ncfile=True)
    #         diags.amoc.MOM6(vhFile, ocean_hgrid, topog, fYear, "./", "Ocean")
    #     _ = [x.close() for x in [ocean_hgrid, topog, vhFile, gs_tar]]

    # -- Close out the tarfile handle
    tar.close()

    # -- Do performance timing
    try:
        infile = infile.replace("/history/", "/ascii/")
        infile = infile.replace(".nc.tar", ".ascii_out.tar")
        label = "Timing"
        if os.path.exists(infile):
            diags.fms.timing(infile, fYear, "./", label)
    except:
        pass
