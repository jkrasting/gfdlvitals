""" Driver for ESM2 class models """

import tarfile
import warnings

from gfdlvitals import averagers
from gfdlvitals.util.average import generic_driver


__all__ = ["routines"]


def routines(args, infile):
    """Driver routine for ESM2-class models

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

    # -- Atmos
    modules = {
        "atmos_month": "Atmos",
        "atmos_level": "Atmos",
    }
    if any(comp in comps for comp in ["atmos", "all"]):
        averagers.latlon.xr_average(fyear, tar, modules)

    # -- Land
    # modules = {"land_month": "Land"}
    # if any(comp in comps for comp in ["land", "all"]):
    #    generic_driver(
    #        fyear,
    #        tar,
    #        modules,
    #        averagers.land_lm3.average,
    #        static_file=("land_static", "land_month"),
    #    )

    # -- Ice
    # modules = {"ice_month": "Ice"}
    # if any(comp in comps for comp in ["ice", "all"]):
    #    averagers.ice.xr_average(fyear, tar, modules)

    # -- Ocean
    modules = {
        "ocean_month": "Ocean",
    }
    if any(comp in comps for comp in ["ocean", "all"]):
        averagers.tripolar.xr_average(fyear, tar, modules)

    # -- OBGC
    modules = {
        "ocean_topaz_fluxes": "OBGC",
        "ocean_topaz_misc": "OBGC",
        "ocean_topaz_sfc_100": "OBGC",
        "ocean_topaz_tracers_month_z": "OBGC",
        "ocean_topaz_wc_btm": "OBGC",
    }
    if any(comp in comps for comp in ["obgc", "all"]):
        averagers.tripolar.xr_average(fyear, tar, modules)

    if any(comp in comps for comp in ["amoc"]):
        warnings.warn("AMOC calculation is not supported for ESM2.")

    # -- Close out the tarfile handle
    tar.close()
