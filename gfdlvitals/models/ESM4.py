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
    #generic_cubesphere_driver(
    #    fYear, tar, modules, averagers.land_lm4.average, grid_spec="land_static"
    #)

    ## ## data_files = [netcdf.extract_from_tar(tar,f"{fyear}.land_month.tile{x}.nc") for x in range(1,7)]
    ## ## data_files = [netcdf.in_mem_xr(x) for x in data_files]
    ## ## dset = xr.concat(data_files,"tile")
    
    ## ## # Retain only time-dependent variables
    ## ## variables = list(dset.variables.keys())
    ## ## for x in variables:
    ## ##     if "time" not in dset[x].dims:
    ## ##         del dset[x]
    
    ## ## # Load grid data
    ## ## grid_files = [netcdf.extract_from_tar(tar,f"{fyear}.land_static.tile{x}.nc") for x in range(1,7)]
    ## ## grid_files = [netcdf.in_mem_xr(x) for x in grid_files]
    ## ## ds_grid = xr.concat(grid_files,"tile")
    
    ## ## # Retain only time-invariant area fields
    ## ## grid = xr.Dataset()
    ## ## variables = list(ds_grid.variables.keys())
    ## ## for x in variables:
    ## ##     if "area" in x or "frac" in x:
    ## ##         grid[x] = ds_grid[x]
    
    ## ## # Get List of cell measures
    ## ## cell_measures = [dset[x].attrs['cell_measures'] for x in list(dset.variables) if "cell_measures" in list(dset[x].attrs.keys())]
    ## ## cell_measures = sorted(list(set(cell_measures)))
    
    ## ## # Create dict of land groups based on cell measures
    ## ## land_groups = {}
    ## ## for x in cell_measures:
    ## ##     land_groups[x] = xr.Dataset()
    
    ## ## # Loop over variables and assign them to groups
    ## ## variables = list(dset.variables.keys())
    ## ## for x in variables:
    ## ##     if "cell_measures" in list(dset[x].attrs.keys()):
    ## ##         _measure = dset[x].attrs["cell_measures"]
    ## ##         land_groups[_measure][x] = dset[x]
    
    ## ## # Since natural tile area is time-dependent, ignore for now
    ## ## if "area: area_ntrl" in cell_measures:
    ## ##     cell_measures.remove("area: area_ntrl")
    
    ## ## # Loop over groups
    ## ## for measure in cell_measures:
    ## ##     _dset = land_groups[measure]
    ## ##     
    ## ##     _measure = measure.split(" ")[-1]
    ## ##     _area = ds_grid[_measure]
    ## ##     
    ## ##     areasum = _area.sum()
    ## ##     global_weights = dset.average_DT.astype("float") * _area
    ## ##     
    ## ##     for region in ['global','nh','sh','tropics']:
    ## ##         weights = xr_mask_weights(global_weights,ds_grid.geolat_t,region=region)
    ## ##         _dset_weighted = xr_weighted_avg(dset,global_weights)
    ## ##         xr_to_db(_dset_weighted,f"{fyear}.{region}AveLand.db")

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
