import tarfile
from gfdlvitals import averagers
from gfdlvitals.util.netcdf import extract_from_tar

from gfdlvitals import averagers
from gfdlvitals import diags
from gfdlvitals.util import extract_ocean_scalar
from gfdlvitals.util.netcdf import extract_from_tar
from gfdlvitals.util.netcdf import tar_member_exists

from gfdlvitals.util.average import generic_driver

import gfdlvitals.util.netcdf as nctools

__all__ = ["routines"]


def routines(args, infile):
    # -- Open the tarfile
    tar = tarfile.open(infile)
    members = tar.getnames()
    # -- Set the model year string
    fyear = str(infile.split("/")[-1].split(".")[0])
    print("Processing " + fyear)

    # -- Atmos
    modules = {
        "atmos_month": "Atmos",
        "atmos_level": "Atmos",
    }
    averagers.latlon.xr_average(fyear, tar, modules)

    # -- Land
    modules = {"land_month": "Land"}
    generic_driver(
        fyear,
        tar,
        modules,
        averagers.land_lm3.average,
        static_file=("land_static", "land_month"),
    )

    # -- Ice
    modules = {"ice_month": "Ice"}
    averagers.ice.xr_average(fyear, tar, modules)

    # -- Ocean
    modules = {
        "ocean_month": "Ocean",
    }
    averagers.tripolar.xr_average(fyear, tar, modules)

    # -- OBGC
    modules = {
        "ocean_topaz_fluxes": "OBGC",
        "ocean_topaz_misc": "OBGC",
        "ocean_topaz_sfc_100": "OBGC",
        "ocean_topaz_tracers_month_z": "OBGC",
        "ocean_topaz_wc_btm": "OBGC",
    }
    averagers.tripolar.xr_average(fyear, tar, modules)

    # -- Close out the tarfile handle
    tar.close()
