""" Command Line Script for running gfdlvitals """

import argparse
import glob
import os
import shutil
import subprocess
import tempfile
import gfdlvitals

__all__ = ["arguments", "process_year", "run"]


def arguments(args=None):
    """
    Function to capture the user-specified command line options
    """
    description = """
    Program for generating global mean statistics directly 
    from history tarfile.

    For help, contact John.Krasting@noaa.gov

    """

    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "historydir",
        metavar="HISTORY DIR",
        type=str,
        default=os.getcwd(),
        help="Path to /history directory",
    )

    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default="./",
        help="Output directory. Default is current directory",
    )

    parser.add_argument(
        "-m",
        "--modelclass",
        type=str,
        default="CM4",
        help="Model class. Options include CM4 and  ESM2. Default is CM4",
    )

    parser.add_argument(
        "-c",
        "--component",
        type=str,
        default="all",
        help="Comma-separated list of components to process. "
        + "See documentation for full list. Default is all.",
    )

    parser.add_argument(
        "-s",
        "--startyear",
        type=int,
        default=None,
        help="Starting year to process. Default is all years.",
    )

    parser.add_argument(
        "-e",
        "--endyear",
        type=int,
        default=None,
        help="Ending year to process. Default is all years.",
    )

    parser.add_argument(
        "-g",
        "--gridspec",
        type=str,
        default=None,
        help="Path to gridspec tarfile. Used in AMOC calculation. " + "Default is None",
    )

    args = parser.parse_args(args)
    args.historydir = os.path.abspath(args.historydir)
    if args.gridspec is not None:
        args.gridspec = os.path.abspath(args.gridspec)

    return args


def process_year(args, infile):
    """Function to process a single year

    Parameters
    ----------
    args : argparse.parser
        Parsed commmand line arguments
    infile : str, pathlike
        History tar file path
    """

    # -- Set the model year string
    fyear = str(infile.split("/")[-1].split(".")[0])

    # -- Run the main code
    if args.modelclass == "ESM2":
        gfdlvitals.models.ESM2.routines(args, infile)
    elif args.modelclass == "CM4":
        gfdlvitals.models.CM4.routines(args, infile)

    # -- Move results to their final location
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    for reg in ["global", "nh", "sh", "tropics"]:
        for component in [
            "Land",
            "Atmos",
            "AtmosAer",
            "AeroCMIP",
            "Ocean",
            "Ice",
            "TOPAZ",
            "COBALT",
            "BLING",
            "OBGC",
            "Timing",
        ]:
            if os.path.exists(fyear + "." + reg + "Ave" + component + ".db"):
                if not os.path.exists(
                    args.outdir + "/" + reg + "Ave" + component + ".db"
                ):
                    shutil.copyfile(
                        fyear + "." + reg + "Ave" + component + ".db",
                        args.outdir + "/" + reg + "Ave" + component + ".db",
                    )
                else:
                    gfdlvitals.util.merge.merge(
                        fyear + "." + reg + "Ave" + component + ".db",
                        args.outdir + "/" + reg + "Ave" + component + ".db",
                    )


def run(args):
    """Function to run the command line tool

    Parameters
    ----------
    args : list
        List of arguments to parse
    """
    cliargs = arguments(args)

    cliargs.outdir = os.path.abspath(cliargs.outdir)

    # -- Get a list of history files
    dirlist = sorted(glob.glob(cliargs.historydir + "/*.tar"))

    # -- Apply start and end year limits, if applicable
    infiles = []
    if (cliargs.startyear is not None) or (cliargs.endyear is not None):
        if cliargs.startyear is None:
            cliargs.startyear = -1
        if cliargs.endyear is None:
            cliargs.endyear = 99999
        for f in dirlist:
            yr = int(os.path.basename(f)[0:4])
            if cliargs.startyear <= yr <= cliargs.endyear:
                infiles.append(f)
    else:
        infiles = dirlist

    # -- DMGET the history files
    if shutil.which("dmget") is not None:
        print("Dmgetting files ...")
        subprocess.call(["dmget"] + infiles)
        print("Complete!")

    # -- Make temporary directory to work in
    cwd = os.getcwd()
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)

    # -- Split list of components to process
    cliargs.component = cliargs.component.split(",")

    # -- Loop over history files
    for _infile in infiles:
        process_year(cliargs, _infile)

    # -- Clean up
    os.chdir(cwd)
    shutil.rmtree(tempdir)
