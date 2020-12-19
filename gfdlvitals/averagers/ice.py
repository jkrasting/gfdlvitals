""" Ice model averaging routines """

import multiprocessing

from functools import partial

import numpy as np

from gfdlvitals.util.average import RichVariable
from gfdlvitals.util.average import process_var

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as netcdf

import warnings

import xarray as xr
__all__ = ["average", "xr_average"]

def xr_average(fyear, tar, modules):
    members = [
        x for x in modules if netcdf.tar_member_exists(tar, f"{fyear}.{x}.nc")
    ]

    for member in members:
        print(f"{fyear}.{member}.nc")
        data_file = netcdf.extract_from_tar(tar,f"{fyear}.ice_month.nc")
        dset = netcdf.in_mem_xr(data_file)
    
        grid_file = f"{fyear}.ice_static.nc" if netcdf.tar_member_exists(tar,f"{fyear}.ice_static.nc") else f"{fyear}.ice_month.nc"
        grid_file = netcdf.extract_from_tar(tar,grid_file)
        ds_grid = netcdf.in_mem_xr(grid_file)

        # Retain only time-dependent variables
        variables = list(dset.variables.keys())
        for x in variables:
            if "time" not in dset[x].dims:
                del dset[x]
            if x == "CN":
                attrs = dset[x].attrs
                dset[x] = dset[x].sum(("ct")).assign_attrs(dset[x].attrs)

        if "CN" in list(dset.variables.keys()):
            concentration = dset["CN"]
        elif "siconc" in list(dset.variables.keys()):
            concentration = dset["siconc"]
        else:
            warnings.warn("Unable to determine sea ice concentation")

        earth_radius = 6371.0e3  # Radius of the Earth in 'm'
        _area = ds_grid["CELL_AREA"] * 4.0 * np.pi * (earth_radius ** 2)
    
        #--- todo Add in concentration and extent
    
        for region in ['global','nh','sh']:
            _masked_area = gmeantools.xr_mask_by_latitude(_area,ds_grid.GEOLAT,region=region)
            gmeantools.write_sqlite_data(f"{fyear}.{region}Ave{modules[member]}.db","area",fyear,_masked_area.sum().data)

            # area-weight but not time_weight
            weights = _masked_area
            _dset = dset.copy()


            ones = (concentration * 0.) + 1.0
            ice_area = (ones.where(concentration>0.,0.)*_masked_area)
            extent = (ones.where(concentration>0.15,0.)*_masked_area)

            ice_area_attrs = {"long_name":"area covered by sea ice","units":"million km2"}
            extent_attrs = {"long_name":"sea ice extent","units":"million km2"}

            for x in list(_dset.variables):
                if tuple(_dset[x].dims)[-3::] == ('time','yT', 'xT'):
                    _dset[x] = ((_dset[x]*weights).sum(('yT','xT'))/weights.sum()).assign_attrs(dset[x].attrs)
                    _dset["ice_area"] = (ice_area.sum(('yT','xT'))*1.e-12).assign_attrs(ice_area_attrs)
                    _dset["extent"] = (extent.sum(('yT','xT'))*1.e-12).assign_attrs(extent_attrs)
                elif tuple(_dset[x].dims)[-3::] == ('time', 'yt', 'xt'):
                    _dset[x] = ((_dset[x]*weights).sum(('yt','xt'))/weights.sum()).assign_attrs(dset[x].attrs)
                    _dset["ice_area"] = (ice_area.sum(('yt','xt'))*1.e-12).assign_attrs(ice_area_attrs)
                    _dset["extent"] = (extent.sum(('yt','xt'))*1.e-12).assign_attrs(extent_attrs)
                else:
                    del _dset[x]



            _dset_max = _dset.max(("time"))
            newvars = dict([(x,x+"_max") for x in list(_dset_max.variables)])
            _dset_max = _dset_max.rename(newvars)

            _dset_min = _dset.min(("time"))
            newvars = dict([(x,x+"_min") for x in list(_dset_min.variables)])
            _dset_min = _dset_min.rename(newvars)

            weights = dset.average_DT.astype("float")
            _dset_weighted = gmeantools.xr_weighted_avg(_dset,weights)
            newvars = dict([(x,x+"_mean") for x in list(_dset_weighted.variables)])
            _dset_weighted = _dset_weighted.rename(newvars)
            gmeantools.xr_to_db(_dset_weighted,fyear,f"{fyear}.{region}AveIce.db")
            gmeantools.xr_to_db(_dset_max,fyear,f"{fyear}.{region}AveIce.db")
            gmeantools.xr_to_db(_dset_min,fyear,f"{fyear}.{region}AveIce.db")
    
def average(grid_file, data_file, fyear, out, lab):
    """Mid-level averaging routine

    Parameters
    ----------
    gs_tl : list of bytes
        Gridspec tiles
    da_tl : list of bytes
        Data tiles
    fyear : str
        Year being processed
    out : str
        Output path directory
    lab : [type]
        DB file name
    """

    _grid_file = netcdf.in_mem_nc(grid_file)
    _data_file = netcdf.in_mem_nc(data_file)

    geolon = _grid_file.variables["GEOLON"][:]
    geolat = _grid_file.variables["GEOLAT"][:]

    average_dt = _data_file.variables["average_DT"][:]

    if "CELL_AREA" in _grid_file.variables.keys():
        earth_radius = 6371.0e3  # Radius of the Earth in 'm'
        cell_area = _grid_file.variables["CELL_AREA"][:] * (
            4.0 * np.pi * (earth_radius ** 2)
        )
    elif "area" in _grid_file.variables.keys():
        cell_area = _grid_file.variables["area"][:]
    else:
        print("FATAL: unable to determine cell area used in ice model")

    if "siconc" in _data_file.variables.keys():
        concentration = _data_file.variables["siconc"][:]
    elif "CN" in _data_file.variables.keys():
        concentration = np.ma.sum(_data_file.variables["CN"][:], axis=-3)
    else:
        print("FATAL: unable to determine ice concentration")

    geolat = np.tile(geolat[None, :], (concentration.shape[0], 1, 1))
    geolon = np.tile(geolon[None, :], (concentration.shape[0], 1, 1))
    cell_area = np.tile(cell_area[None, :], (concentration.shape[0], 1, 1))

    for reg in ["global", "nh", "sh"]:
        sqlite_out = out + "/" + fyear + "." + reg + "Ave" + lab + ".db"
        variables = []
        # area and extent in million square km
        _conc, _area = gmeantools.mask_latitude_bands(
            concentration, cell_area, geolat, region=reg
        )
        variables.append(
            ("area", (np.ma.sum((_conc * _area), axis=(-1, -2)) * 1.0e-12))
        )
        variables.append(
            (
                "extent",
                (
                    np.ma.sum(
                        (np.ma.where(np.greater(_conc, 0.15), _area, 0.0)),
                        axis=(-1, -2),
                    )
                    * 1.0e-12
                ),
            )
        )
        for vname in variables:
            gmeantools.write_sqlite_data(
                sqlite_out,
                vname[0] + "_mean",
                fyear[:4],
                np.ma.average(vname[1], weights=average_dt),
            )
            gmeantools.write_sqlite_data(
                sqlite_out, vname[0] + "_max", fyear[:4], np.ma.max(vname[1])
            )
            gmeantools.write_sqlite_data(
                sqlite_out, vname[0] + "_min", fyear[:4], np.ma.min(vname[1])
            )

    variables = list(_data_file.variables.keys())
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
            cell_area,
            average_dt=average_dt,
        )
        for x in variables
    ]

    _grid_file.close()
    _data_file.close()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(partial(process_var, **{"averager": "ice"}), variables)
