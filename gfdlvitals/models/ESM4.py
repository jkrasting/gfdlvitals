import os
import tarfile

from gfdlvitals import averagers
from gfdlvitals import diags
from gfdlvitals.util import extract_ocean_scalar
from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists

import gfdlvitals.util.netcdf as nctools

__all__ = ["routines"]


def routines(args, infile):

    # -- Open the tarfile
    tar = tarfile.open(infile)
    members = tar.getnames()

    # -- Set the model year string
    fYear = str(infile.split("/")[-1].split(".")[0])
    print("Processing " + fYear)

    # -- Atmospheric Fields
    modules = {
        "atmos_month": "Atmos",
        "atmos_co2_month": "Atmos",
        "atmos_month_aer": "AtmosAer",
        "aerosol_month_cmip": "AeroCMIP",
    }
    averagers.cubesphere.driver(fYear, tar, modules)

    # -- Land Fields
    modules = {"land_month": "Land"}
    averagers.land_lm4.driver(fYear, tar, modules)

    # -- Ice
    modules = {"ice_month": "Ice"}
    averagers.ice.driver(fYear, tar, modules)

    # -- Ocean
    fname = f"{fYear}.ocean_scalar_annual.nc"
    if tar_member_exists(tar, fname):
        print(f"{fYear} - ocean_scalar_annual")
        fdata = nctools.extract_from_tar(tar, fname, ncfile=True)
        extract_ocean_scalar.mom6(fdata, fYear, "./")
        fdata.close()

    # -- AMOC
    if args.gridspec is not None:
        gs_tar = tarfile.open(args.gridspec)
        ocean_hgrid = extract_from_tar(gs_tar, "ocean_hgrid.nc", ncfile=True)
        topog = extract_from_tar(gs_tar, "ocean_topog.nc", ncfile=True)
        fname = f"{fYear}.ocean_annual_z.nc"
        if tar_member_exists(tar, fname):
            vhFile = extract_from_tar(tar, fname, ncfile=True)
            diags.amoc.MOM6(vhFile, ocean_hgrid, topog, fYear, "./", "Ocean")
        _ = [x.close() for x in [ocean_hgrid, topog, vhFile, gs_tar]]

    # -- Close out the tarfile handle
    tar.close()

    # # -- COBALT
    # label = "COBALT"
    # modules = [
    #     "ocean_cobalt_sfc",
    #     "ocean_cobalt_misc",
    #     "ocean_cobalt_tracers_year",
    #     "ocean_cobalt_tracers_int",
    # ]
    # fgs = None
    # if modifier + fYear + ".ocean_static.nc" in members:
    #     fgs = extract_from_tar(tar, modifier + fYear + ".ocean_static.nc")
    # elif modifier + fYear + ".ocean_month.nc" in members:
    #     fgs = extract_from_tar(tar, modifier + fYear + ".ocean_month.nc")
    # if fgs is not None:
    #     for module in modules:
    #         fname = modifier + fYear + "." + module + ".nc"
    #         if fname in members:
    #             fdata = extract_from_tar(tar, fname)
    #             print(fname)
    #             averagers.tripolar.average(fgs, fdata, fYear, "./", label)
    #             fdata.close()
    #     fgs.close()

    # # -- BLING
    # label = "BLING"
    # modules = [
    #     "ocean_bling",
    #     "ocean_bling_cmip6_omip_2d",
    #     "ocean_bling_cmip6_omip_rates_year_z",
    #     "ocean_bling_cmip6_omip_sfc",
    #     "ocean_bling_cmip6_omip_tracers_month_z",
    #     "ocean_bling_cmip6_omip_tracers_year_z",
    # ]
    # fgs = None
    # if modifier + fYear + ".ocean_static.nc" in members:
    #     fgs = extract_from_tar(tar, modifier + fYear + ".ocean_static.nc")
    # elif modifier + fYear + ".ocean_month.nc" in members:
    #     fgs = extract_from_tar(tar, modifier + fYear + ".ocean_month.nc")
    # if fgs is not None:
    #     for module in modules:
    #         fname = modifier + fYear + "." + module + ".nc"
    #         if fname in members:
    #             fdata = extract_from_tar(tar, fname)
    #             print(fname)
    #             averagers.tripolar.average(fgs, fdata, fYear, "./", label)
    #             fdata.close()
    #     fgs.close()
    # -- Do performance timing

    try:
        infile = infile.replace("/history/", "/ascii/")
        infile = infile.replace(".nc.tar", ".ascii_out.tar")
        label = "Timing"
        if os.path.exists(infile):
            diags.fms.timing(infile, fYear, "./", label)
    except:
        pass
