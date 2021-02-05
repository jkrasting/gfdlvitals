""" Routine for calculating AMOC """

import sys
import numpy as np
from gfdlvitals.util import gmeantools
from . import m6toolbox


__all__ = ["mom6"]


def mom6(vh_file, f_ocean_hgrid, f_topog, fyear, outdir, label):
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
