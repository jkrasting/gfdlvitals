import tarfile
from gfdlvitals import averagers
from gfdlvitals.util.netcdf import extract_from_tar

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

    # -- Land
    modules = {"land_month": "Land"}
    averagers.land_lm3.driver(fYear, tar, modules)

    # -- Atmos
    modules = {
        "atmos_month": "Atmos",
        "atmos_level": "Atmos",
    }
    averagers.latlon.driver(fYear, tar, modules)

    # -- Ice
    modules = {"ice_month": "Ice"}
    averagers.ice.driver(fYear, tar, modules)

    # -- Ocean
    modules = {
        "ocean_month": "Ocean",
    }
    averagers.tripolar.driver(fYear, tar, modules)

    # -- OBGC
    modules = {
        "ocean_topaz_fluxes": "OBGC",
        "ocean_topaz_misc": "OBGC",
        "ocean_topaz_sfc_100": "OBGC",
        "ocean_topaz_tracers_month_z": "OBGC",
        "ocean_topaz_wc_btm": "OBGC",
    }
    averagers.tripolar.driver(fYear, tar, modules)

    # -- Close out the tarfile handle
    tar.close()
