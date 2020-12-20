""" Driver for ESM2 class models """

import tarfile

from gfdlvitals import averagers
from gfdlvitals.util.average import generic_driver


__all__ = ["routines"]


def routines(infile):
    """Driver routine for ESM2-class models

    Parameters
    ----------
    infile : str, pathlike
        History tar file path
    """

    # -- Open the tarfile
    tar = tarfile.open(infile)

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
