"""Land LM4.1 Averaging Routines"""

import multiprocessing
import re

from functools import partial

import numpy as np

from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ["average"]


def average(grid_file, data_file, fyear, out, lab):
    """Mid-level averaging routine

    Parameters
    ----------
    grid_file : list of bytes
        Gridspec tiles
    data_file : list of bytes
        Data tiles
    fyear : str
        Year being processed
    out : str
        Output path directory
    lab : [type]
        DB file name
    """
    _grid_file = [nctools.in_mem_nc(x) for x in grid_file]
    _data_file = [nctools.in_mem_nc(x) for x in data_file]

    for land_file in [_data_file, _grid_file]:
        if "geolat_t" in land_file[0].variables:
            geolat = gmeantools.cube_sphere_aggregate("geolat_t", _data_file)
            geolon = gmeantools.cube_sphere_aggregate("geolon_t", _data_file)
            break

    area_types = {}
    for land_file in [_data_file, _grid_file]:
        for variable in sorted(land_file[0].variables):
            if re.match(r".*_area", variable) or re.match(r"area.*", variable):
                # for now, skip the area variables that depend on time
                timedependent = False
                for dimension in land_file[0].variables[variable].dimensions:
                    timedependent = (
                        timedependent
                        or land_file[0].dimensions[dimension].isunlimited()
                    )
                if not timedependent:
                    if variable not in area_types.keys():
                        area_types[variable] = gmeantools.cube_sphere_aggregate(
                            variable, land_file
                        )

    depth = _data_file[0].variables["zhalf_soil"][:]
    cell_depth = []
    for i in range(1, len(depth)):
        thickness = round((depth[i] - depth[i - 1]), 2)
        cell_depth.append(thickness)
    cell_depth = np.array(cell_depth)

    variables = list(_data_file[0].variables.keys())
    variables = [
        RichVariable(
            x,
            grid_file,
            data_file,
            fyear,
            out,
            lab,
            geolat,
            geolon,
            area_types=area_types,
            cell_depth=cell_depth,
        )
        for x in variables
    ]

    _ = [x.close() for x in _grid_file]
    _ = [x.close() for x in _data_file]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "land_lm4"}), variables)
