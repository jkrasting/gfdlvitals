""" Ice model averaging routines """

import warnings

import numpy as np

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.xrtools as xrtools
import gfdlvitals.util.netcdf as netcdf


__all__ = ["xr_average"]


def xr_average(fyear, tar, modules):
    """xarray-based processing routines for lat-lon model output

    Parameters
    ----------
    fyear : str
        Year being processed (YYYY)
    tar : tarfile
        In-memory tarfile object
    modules : dict
        Mappings of netCDF file names inside the tar file to output db file names
    """

    members = [x for x in modules if netcdf.tar_member_exists(tar, f"{fyear}.{x}.nc")]

    for member in members:
        print(f"{fyear}.{member}.nc")
        data_file = netcdf.extract_from_tar(tar, f"{fyear}.ice_month.nc")
        dset = netcdf.in_mem_xr(data_file)

        if netcdf.tar_member_exists(tar, f"{fyear}.ice_static.nc"):
            grid_file = f"{fyear}.ice_static.nc"
        elif netcdf.tar_member_exists(tar, f"{fyear}.sea_ice_geometry.nc"):
            grid_file = f"{fyear}.sea_ice_geometry.nc"
        else:
            grid_file = f"{fyear}.ice_month.nc"

        grid_file = netcdf.extract_from_tar(tar, grid_file)
        ds_grid = netcdf.in_mem_xr(grid_file)

        # Retain only time-dependent variables
        variables = list(dset.variables.keys())
        for x in variables:
            if "time" not in dset[x].dims:
                del dset[x]
            if x == "CN":
                dset[x] = dset[x].sum(("ct")).assign_attrs(dset[x].attrs)

        if "CN" in list(dset.variables.keys()):
            concentration = dset["CN"]
        elif "siconc" in list(dset.variables.keys()):
            concentration = dset["siconc"]
        else:
            warnings.warn("Unable to determine sea ice concentation")

        if "Ah" in ds_grid.variables:
            ice_area_units = str(ds_grid.Ah.units)
            assert (
                ice_area_units == "m2"
            ), f"Ice area units {ice_area_units} are not correct. Expected m2"
            _area = ds_grid.Ah
            _area = _area.rename({"lath": "yT", "lonh": "xT"})
        else:
            earth_radius = 6371.0e3  # Radius of the Earth in 'm'
            if "CELL_AREA" not in ds_grid.variables:
                warnings.warn("Unable to find sea ice cell area. Skipping.")
                return

            _area = ds_grid["CELL_AREA"] * 4.0 * np.pi * (earth_radius**2)

        # --- todo Add in concentration and extent

        for region in ["global", "nh", "sh"]:

            if "geolat" in ds_grid.variables:
                _geolat = ds_grid["geolat"]
                _geolat = _geolat.rename({"lath": "yT", "lonh": "xT"})
            else:
                _geolat = ds_grid["GEOLAT"]

            _masked_area = xrtools.xr_mask_by_latitude(_area, _geolat, region=region)
            gmeantools.write_sqlite_data(
                f"{fyear}.{region}Ave{modules[member]}.db",
                "area",
                fyear,
                _masked_area.sum().data,
            )

            # area-weight but not time_weight
            weights = _masked_area
            _dset = dset.copy()

            ones = (concentration * 0.0) + 1.0
            ice_area = ones.where(concentration > 0.0, 0.0) * _masked_area
            extent = ones.where(concentration > 0.15, 0.0) * _masked_area

            ice_area_attrs = {
                "long_name": "area covered by sea ice",
                "units": "million km2",
            }
            extent_attrs = {"long_name": "sea ice extent", "units": "million km2"}

            for x in list(_dset.variables):
                if tuple(_dset[x].dims)[-3::] == ("time", "yT", "xT"):
                    _dset[x] = (
                        (_dset[x] * weights).sum(("yT", "xT")) / weights.sum()
                    ).assign_attrs(dset[x].attrs)
                    _dset["ice_area"] = (
                        ice_area.sum(("yT", "xT")) * 1.0e-12
                    ).assign_attrs(ice_area_attrs)
                    _dset["extent"] = (extent.sum(("yT", "xT")) * 1.0e-12).assign_attrs(
                        extent_attrs
                    )
                elif tuple(_dset[x].dims)[-3::] == ("time", "yt", "xt"):
                    _dset[x] = (
                        (_dset[x] * weights).sum(("yt", "xt")) / weights.sum()
                    ).assign_attrs(dset[x].attrs)
                    _dset["ice_area"] = (
                        ice_area.sum(("yt", "xt")) * 1.0e-12
                    ).assign_attrs(ice_area_attrs)
                    _dset["extent"] = (extent.sum(("yt", "xt")) * 1.0e-12).assign_attrs(
                        extent_attrs
                    )
                else:
                    del _dset[x]

            _dset_max = _dset.max(("time"))
            newvars = {x: x + "_max" for x in list(_dset_max.variables)}
            _dset_max = _dset_max.rename(newvars)

            _dset_min = _dset.min(("time"))
            newvars = {x: x + "_min" for x in list(_dset_min.variables)}
            _dset_min = _dset_min.rename(newvars)

            weights = dset.average_DT.astype("float")
            _dset_weighted = xrtools.xr_weighted_avg(_dset, weights)
            newvars = {x: x + "_mean" for x in list(_dset_weighted.variables)}
            _dset_weighted = _dset_weighted.rename(newvars)

            xrtools.xr_to_db(_dset_weighted, fyear, f"{fyear}.{region}AveIce.db")
            xrtools.xr_to_db(_dset_max, fyear, f"{fyear}.{region}AveIce.db")
            xrtools.xr_to_db(_dset_min, fyear, f"{fyear}.{region}AveIce.db")
