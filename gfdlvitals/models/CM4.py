""" Driver for CM4 class models """

import os
import tarfile

from gfdlvitals import averagers
from gfdlvitals import diags
from gfdlvitals.util import extract_ocean_scalar
from gfdlvitals.util.netcdf import tar_member_exists

import gfdlvitals.util.netcdf as nctools


__all__ = ["routines"]


def routines(args, infile):
    """Driver routine for CM4-class models

    Parameters
    ----------
    args : argparse.parser
        Parsed commmand line arguments
    infile : str, pathlike
        History tar file path
    """

    # -- Open the tarfile
    tar = tarfile.open(infile)

    # -- Set the model year string
    fyear = str(infile.split("/")[-1].split(".")[0])
    print("Processing " + fyear)

    # -- Get list of components to process
    comps = args.component

    # -- Atmospheric Fields
    modules = {
        "atmos_month": "Atmos",
        "atmos_co2_month": "Atmos",
        "atmos_month_aer": "AtmosAer",
        "aerosol_month_cmip": "AeroCMIP",
    }
    if any(comp in comps for comp in ["atmos", "all"]):
        averagers.cubesphere.xr_average(fyear, tar, modules)

    # -- Land Fields
    modules = {"land_month": "Land"}
    if any(comp in comps for comp in ["land", "all"]):
        averagers.land_lm4.xr_average(fyear, tar, modules)

    # -- Ice
    modules = {"ice_month": "Ice"}
    if any(comp in comps for comp in ["ice", "all"]):
        averagers.ice.xr_average(fyear, tar, modules)

    # -- Ocean
    fname = f"{fyear}.ocean_scalar_annual.nc"
    if any(comp in comps for comp in ["ocean", "all"]):
        if tar_member_exists(tar, fname):
            print(f"{fyear}.ocean_scalar_annual.nc")
            fdata = nctools.extract_from_tar(tar, fname, ncfile=True)
            extract_ocean_scalar.mom6(fdata, fyear, "./")
            fdata.close()

    # -- OBGC
    modules = {
        "ocean_cobalt_sfc": "OBGC",
        "ocean_cobalt_misc": "OBGC",
        "ocean_cobalt_tracers_year": "OBGC",
        "ocean_cobalt_tracers_int": "OBGC",
        "ocean_bling": "OBGC",
        "ocean_bling_cmip6_omip_2d": "OBGC",
        "ocean_bling_cmip6_omip_rates_year_z": "OBGC",
        "ocean_bling_cmip6_omip_sfc": "OBGC",
        "ocean_bling_cmip6_omip_tracers_month_z": "OBGC",
        "ocean_bling_cmip6_omip_tracers_year_z": "OBGC",
    }
    if any(comp in comps for comp in ["obgc", "all"]):
        averagers.tripolar.xr_average(fyear, tar, modules)

    # -- AMOC
    if any(comp in comps for comp in ["amoc", "all"]):
        diags.amoc.mom6_amoc(fyear, tar)

    # -- Close out the tarfile handle
    tar.close()

    # -- Do performance timing
    # try:
    #    infile = infile.replace("/history/", "/ascii/")
    #    infile = infile.replace(".nc.tar", ".ascii_out.tar")
    #    label = "Timing"
    #    if os.path.exists(infile):
    #        diags.fms.timing(infile, fyear, "./", label)
    # except RuntimeError:
    #    pass
