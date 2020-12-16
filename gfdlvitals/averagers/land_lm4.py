"""Land LM4.1 Averaging Routines"""

import multiprocessing
import re

from functools import partial

import numpy as np
import xarray as xr

from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as netcdf

__all__ = ["average", "xr_average"]


def xr_average(fyear, tar, modules):
    members = [
        x for x in modules if netcdf.tar_member_exists(tar, f"{fyear}.{x}.tile1.nc")
    ]

    for member in members:
        print(f"{fyear}.{member}.nc")
        data_files = [
            netcdf.extract_from_tar(tar, f"{fyear}.{member}.tile{x}.nc")
            for x in range(1, 7)
        ]
        data_files = [netcdf.in_mem_xr(x) for x in data_files]
        dset = xr.concat(data_files, "tile")

        # Retain only time-dependent variables
        variables = list(dset.variables.keys())
        for x in variables:
            if "time" not in dset[x].dims:
                del dset[x]

        # Load grid data
        grid_files = [
            netcdf.extract_from_tar(tar, f"{fyear}.land_static.tile{x}.nc")
            for x in range(1, 7)
        ]
        grid_files = [netcdf.in_mem_xr(x) for x in grid_files]
        ds_grid = xr.concat(grid_files, "tile")

        # Retain only time-invariant area fields
        grid = xr.Dataset()
        variables = list(ds_grid.variables.keys())
        for x in variables:
            if "area" in x or "frac" in x:
                grid[x] = ds_grid[x]

        # Get List of cell measures
        cell_measures = [
            dset[x].attrs["cell_measures"]
            for x in list(dset.variables)
            if "cell_measures" in list(dset[x].attrs.keys())
        ]
        cell_measures = sorted(list(set(cell_measures)))

        # Create dict of land groups based on cell measures
        land_groups = {}
        for x in cell_measures:
            land_groups[x] = xr.Dataset()

        # Loop over variables and assign them to groups
        variables = list(dset.variables.keys())
        for x in variables:
            if "cell_measures" in list(dset[x].attrs.keys()):
                _measure = dset[x].attrs["cell_measures"]
                land_groups[_measure][x] = dset[x]

        # Since natural tile area is time-dependent, ignore for now
        if "area: area_ntrl" in cell_measures:
            cell_measures.remove("area: area_ntrl")

        # Loop over groups
        for measure in cell_measures:
            _dset = land_groups[measure]

            _measure = measure.split(" ")[-1]
            _area = ds_grid[_measure]

            global_weights = dset.average_DT.astype("float") * _area

            for region in ["global", "nh", "sh", "tropics"]:
                areasum = gmeantools.xr_mask_by_latitude(_area,ds_grid.geolat_t,region=region)
                areasum = areasum.sum().data
                print(_measure,areasum)
                gmeantools.write_sqlite_data(f"{fyear}.{region}Ave{modules[member]}.db",_measure,fyear,areasum)

                weights = gmeantools.xr_mask_by_latitude(
                    global_weights, ds_grid.geolat_t, region=region
                )
                _dset_weighted = gmeantools.xr_weighted_avg(dset, global_weights)
                gmeantools.xr_to_db(
                    _dset_weighted, fyear, f"{fyear}.{region}Ave{modules[member]}.db"
                )


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
    _grid_file = [netcdf.in_mem_nc(x) for x in grid_file]
    _data_file = [netcdf.in_mem_nc(x) for x in data_file]

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
