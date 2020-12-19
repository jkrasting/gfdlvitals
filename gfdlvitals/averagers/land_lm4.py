"""Land LM4.1 Averaging Routines"""

import xarray as xr

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.xrtools as xrtools
import gfdlvitals.util.netcdf as netcdf


__all__ = ["xr_average"]


def xr_average(fyear, tar, modules):
    """xarray-based processing routines for cubed sphere LM4 land output

    Parameters
    ----------
    fyear : str
        Year being processed (YYYY)
    tar : tarfile
        In-memory tarfile object
    modules : dict
        Mappings of netCDF file names inside the tar file to output db file names
    """

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

        # Calculate cell depth
        depth = dset["zhalf_soil"].data
        depth = [depth[x] - depth[x - 1] for x in range(1, len(depth))]
        dset["depth"] = xr.DataArray(depth, dims=("zfull_soil"))
        depth = dset["depth"]

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
                dset[x].attrs["measure"] = _measure.split(" ")[-1]
                land_groups[_measure][x] = dset[x]

        # Since natural tile area is time-dependent, ignore for now
        if "area: area_ntrl" in cell_measures:
            cell_measures.remove("area: area_ntrl")

        if "area: glac_area" in cell_measures:
            cell_measures.remove("area: glac_area")

        # Loop over groups
        for measure in cell_measures:
            _dset = land_groups[measure]

            _measure = measure.split(" ")[-1]
            _area = ds_grid[_measure]

            for region in ["global", "nh", "sh", "tropics"]:
                _masked_area = xrtools.xr_mask_by_latitude(
                    _area, ds_grid.geolat_t, region=region
                )
                gmeantools.write_sqlite_data(
                    f"{fyear}.{region}Ave{modules[member]}.db",
                    _measure,
                    fyear,
                    _masked_area.sum().data,
                )

                # _masked_area = _masked_area.fillna(0)

                weights = dset.average_DT.astype("float") * _masked_area
                if _measure == "soil_area":
                    area_x_depth = _masked_area * depth
                    gmeantools.write_sqlite_data(
                        f"{fyear}.{region}Ave{modules[member]}.db",
                        "soil_volume",
                        fyear,
                        area_x_depth.sum().data,
                    )
                    weights = [
                        weights,
                        (weights * depth).transpose(
                            "tile", "time", "zfull_soil", "grid_yt", "grid_xt"
                        ),
                    ]
                    for x in list(_dset.variables):
                        if "zfull_soil" in list(_dset[x].dims):
                            _dset[x].attrs["measure"] = "soil_volume"

                _dset_weighted = xrtools.xr_weighted_avg(_dset, weights)

                xrtools.xr_to_db(
                    _dset_weighted, fyear, f"{fyear}.{region}Ave{modules[member]}.db"
                )
