""" Routine for calculating AMOC """

import sys
import numpy as np
from gfdlvitals.util import gmeantools
from gfdlvitals.util.netcdf import tar_member_exists
from gfdlvitals.util.netcdf import extract_from_tar
from . import m6toolbox


__all__ = ["mom6"]


def mom6(fyear, gs_tar, tar):
    """Driver for AMOC calculation in MOM6-class models

    Parameters
    ----------
    fyear : str
        Year label (YYYY)
    gs_tar : tarfile
        In-memory gridspec tarfile object
    tar : tarfile
        In-memory history tarfile object
    """

    # Extract ocean hgrid
    ocean_hgrid = (
        extract_from_tar(gs_tar, "ocean_hgrid.nc", ncfile=True)
        if tar_member_exists(gs_tar, "ocean_hgrid.nc")
        else None
    )

    # Extract topog.nc or ocean_topog.nc, in order of preference
    topog = (
        extract_from_tar(gs_tar, "topog.nc", ncfile=True)
        if tar_member_exists(gs_tar, "topog.nc")
        else None
    )
    topog = (
        extract_from_tar(gs_tar, "ocean_topog.nc", ncfile=True)
        if tar_member_exists(gs_tar, "ocean_topog.nc")
        else topog
    )

    if ocean_hgrid is not None and topog is not None:
        fname = f"{fyear}.ocean_annual_z.nc"
        if tar_member_exists(tar, fname):
            vh_file = extract_from_tar(tar, fname, ncfile=True)
            otsfn(vh_file, ocean_hgrid, topog, fyear, "./", "Ocean")
        _ = [x.close() for x in [ocean_hgrid, topog, vh_file, gs_tar]]


def otsfn(vh_file, f_ocean_hgrid, f_topog, fyear, outdir, label):
    """Computes AMOC for MOM6-class models

    Parameters
    ----------
    vh_file : netCDF4.Dataset
        File containing vmo field
    f_ocean_hgrid : netCDF4.Dataset
        File containing grid info
    f_topog : netCDF4.Dataset
        File containing topography
    fyear : str
        Year label (YYYY)
    outdir : str, path-like
        Path to output SQLite file
    label : str
        SQLite output stream name
    """
    if "vmo" in vh_file.variables.keys():
        vh_field = (vh_file.variables["vmo"][0].filled(0)) * 1.0e-9
        zt_coord = vh_file.variables["z_i"][:]
        yq_coord = vh_file.variables["yq"][:]
    else:
        print("amoc.py FATAL: vmo variable not present in ocean_annual_z.nc")
        sys.exit(0)

    # -- Get grid info from gridspec file
    x = f_ocean_hgrid.variables["x"][1::2, 1::2]
    y = f_ocean_hgrid.variables["y"][1::2, 1::2]
    depth = f_topog.variables["depth"][:]
    code = m6toolbox.genBasinMasks(x, y, depth)

    # -- Define atlantic/arctic mask
    atlmask = np.where(np.logical_or(code == 2, code == 4), 1.0, 0.0)

    # -- Compute psi
    psi = m6toolbox.MOCpsi(vh_field, vmsk=atlmask)
    # check if output is symmetric (kludge!)
    yq_coord = yq_coord[1:] if (yq_coord.shape[0] == psi.shape[-1] + 1) else yq_coord
    maxsfn = np.max(
        psi[np.logical_and(zt_coord > 500, zt_coord < 2500)][
            :, np.greater_equal(yq_coord, 20)
        ]
    )
    print("  AMOC = " + str(maxsfn))

    # -- Write to sqlite
    gmeantools.write_sqlite_data(
        outdir + "/" + fyear + ".globalAve" + label + ".db",
        "amoc_vh",
        fyear[:4],
        maxsfn,
    )
