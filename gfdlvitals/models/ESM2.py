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
    fYear = str(infile.split("/")[-1].split(".")[0])
    print("Processing " + fYear)

    # -- Land
    modules = {"land_month": "Land"}
    generic_driver(
        fYear,
        tar,
        modules,
        averagers.land_lm3.average,
        static_file=("land_static", "land_month"),
    )

    # -- Atmos
    modules = {
        "atmos_month": "Atmos",
        "atmos_level": "Atmos",
    }
    generic_driver(fYear, tar, modules, averagers.latlon.average, static_file=None)

    # -- Ice
    modules = {"ice_month": "Ice"}
    generic_driver(
        fYear,
        tar,
        modules,
        averagers.ice.average,
        static_file=("ice_static", "ice_month"),
    )

    # -- Ocean
    modules = {
        "ocean_month": "Ocean",
    }
    generic_driver(
        fYear,
        tar,
        modules,
        averagers.tripolar.average,
        static_file=("ocean_static", "ocean_month"),
    )

    # -- OBGC
    modules = {
        "ocean_topaz_fluxes": "OBGC",
        "ocean_topaz_misc": "OBGC",
        "ocean_topaz_sfc_100": "OBGC",
        "ocean_topaz_tracers_month_z": "OBGC",
        "ocean_topaz_wc_btm": "OBGC",
    }
    generic_driver(
        fYear,
        tar,
        modules,
        averagers.tripolar.average,
        static_file=("ocean_static", "ocean_month"),
    )

    # -- Close out the tarfile handle
    tar.close()
