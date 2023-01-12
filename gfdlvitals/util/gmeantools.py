""" Generic Suite of Utilities """

import math
import pickle
import sqlite3
import warnings

import numpy as np
import pkg_resources as pkgr

__all__ = [
    "get_web_vars_dict",
    "mask_latitude_bands",
    "area_mean",
    "legacy_area_mean",
    "cube_sphere_aggregate",
    "write_sqlite_data",
    "parse_cell_measures",
    "extract_metadata",
    "write_metadata",
]


def get_web_vars_dict():
    """Returns dictionary of legacy LM3 variables

    Returns
    -------
    dict
        LM3 variable module mappings and metadata
    """
    mapping_file = pkgr.resource_filename(
        "gfdlvitals", "resources/LM3_variable_dictionary.pkl"
    )
    return pickle.load(
        open(
            mapping_file,
            "rb",
        )
    )


def mask_latitude_bands(var, cell_area, geolat, region="global"):
    """Masks a variable and associated cell area based on region

    Parameters
    ----------
    var : np.ma.MaskedArray
        Input array
    cell_area : np.ma.MaskedArray
        Array of cell areas
    geolat : np.ma.MaskedArray
        Array of latitude coordinates
    region : str, optional
        Region of "global", "nh", "sh", or "tropics", by default "global"

    Returns
    -------
    np.ma.MaskedArray
        var, cell_area masked by region

    Raises
    ------
    ValueError
        Unknown region specified
    """
    if region == "tropics":
        var = np.ma.masked_where(np.logical_or(geolat < -30.0, geolat > 30.0), var)
        cell_area = np.ma.masked_where(
            np.logical_or(geolat < -30.0, geolat > 30.0), cell_area
        )
    elif region == "nh":
        var = np.ma.masked_where(np.less_equal(geolat, 30.0), var)
        cell_area = np.ma.masked_where(np.less_equal(geolat, 30.0), cell_area)
    elif region == "sh":
        var = np.ma.masked_where(np.greater_equal(geolat, -30.0), var)
        cell_area = np.ma.masked_where(np.greater_equal(geolat, -30.0), cell_area)
    elif region != "global":
        raise ValueError("Unknown region specified.")
    return var, cell_area


def area_mean(
    var,
    cell_area,
    geolat,
    geolon,
    region="global",
    cell_depth=None,
):
    """Computes area mean of a variable

    Parameters
    ----------
    var : np.ma.MaskedArray
        Input array
    cell_area : np.ma.MaskedArray
        Array of cell areas
    geolat : np.ma.MaskedArray
        Array of latitude coordinates
    geolon : np.ma.MaskedArray
        Array of longitude coordinates
    region : str, optional
        Region of "global", "nh", "sh", or "tropics", by default "global"
    cell_depth : np.ma.MaskedArray, optional
        Array of cell depths for 4D-data, by default None

    Returns
    -------
    np.ma.MaskedArray
        Scalar area mean of the variable and cell area
    """
    if cell_depth is not None:
        if var.shape[0] == cell_depth.shape[0]:
            cell_area = np.tile(cell_area[None, :], (cell_depth.shape[0], 1, 1))
            geolat = np.tile(geolat[None, :], (cell_depth.shape[0], 1, 1))
            geolon = np.tile(geolon[None, :], (cell_depth.shape[0], 1, 1))
        else:
            print(
                "Warning: inconsisent dimensions between varname and the cell depth axis.",
                var.shape[0],
                cell_depth.shape[0],
            )
            null_result = np.ma.masked_where(True, 0.0)
            return null_result, null_result
    cell_area = np.ma.array(cell_area)
    cell_area.mask = var.mask
    var, cell_area = mask_latitude_bands(var, cell_area, geolat, region)
    if cell_depth is not None:
        summed = np.ma.sum(
            var
            * cell_area
            * np.tile(cell_depth[:, None, None], (1, var.shape[1], var.shape[2]))
        )
        var = np.ma.average(var, axis=0, weights=cell_depth)
        res = np.ma.sum(var * cell_area) / cell_area.sum()
        return res, summed.sum()
    res = np.ma.sum(var * cell_area) / cell_area.sum()
    return res, cell_area.sum()


def legacy_area_mean(
    var,
    cell_area,
    geolat,
    geolon,
    cell_frac=None,
    soil_frac=None,
    region="global",
    varname=None,
    cell_depth=None,
    component=None,
):
    """Legacy version of area mean calculation

    Parameters
    ----------
    var : np.ma.MaskedArray
        Input array
    cell_area : np.ma.MaskedArray
        Array of cell areas
    geolat : np.ma.MaskedArray
        Array of latitude coordinates
    geolon : np.ma.MaskedArray
        Array of longitude coordinates
    cell_frac : np.ma.MaskedArray, optional
        Array of land cell fraction per grid cell, by default None
    soil_frac : np.ma.MaskedArray, optional
        Array of soil fraction per grid cell, by default None
    region : str, optional
        Region of "global", "nh", "sh", or "tropics", by default "global"
    varname : str, optional
        Variable name, by default None
    cell_depth : np.ma.MaskedArray, optional
        Array of cell depths for 4D-data, by default None
    component : str, optional
        Model component, by default None

    Returns
    -------
    np.ma.MaskedArray
        Scalar area mean of the variable and cell area
    """
    # Land-specific modifications
    if component == "land":
        module_dict = get_web_vars_dict()
        # Read dictionary of keys
        if varname in module_dict.keys():
            module = module_dict[varname]
        elif varname.lower() in module_dict.keys():
            module = module_dict[varname.lower()]
        else:
            module = ""
        # Create a weighting factor
        if module == "vegn":
            cell_area = cell_area * cell_frac * soil_frac
        else:
            cell_area = cell_area * cell_frac
        # Create a 3-D mask if needed
        if cell_depth is not None:
            if var.shape[0] == cell_depth.shape[0]:
                cell_area = np.tile(cell_area[None, :], (cell_depth.shape[0], 1, 1))
                geolat = np.tile(geolat[None, :], (cell_depth.shape[0], 1, 1))
                geolon = np.tile(geolon[None, :], (cell_depth.shape[0], 1, 1))
            else:
                print(
                    "Warning: inconsisent dimensions between varname and the cell depth axis.",
                    var.shape[0],
                    cell_depth.shape[0],
                )
                null_result = np.ma.masked_where(True, 0.0)
                return null_result, null_result
        # Apply data mask to weighting mask
        cell_area.mask = var.mask
    var, cell_area = mask_latitude_bands(var, cell_area, geolat, region)
    # -- Land depth averaging and summation
    if cell_depth is not None:
        summed = np.ma.sum(
            var
            * cell_area
            * np.tile(cell_depth[:, None, None], (1, var.shape[1], var.shape[2]))
        )
        var = np.ma.average(var, axis=0, weights=cell_depth)
        res = np.ma.sum(var * cell_area) / cell_area.sum()
        return res, summed
    res = np.ma.sum(var * cell_area) / cell_area.sum()
    summed = np.ma.sum(var * cell_area)
    return res, summed


def cube_sphere_aggregate(var, tiles):
    """[summary]

    Parameters
    ----------
    var : str
        Variable name
    tiles : netCDF4.Dataset
        Datasets for each cubesphere tile

    Returns
    -------
    np.ma.MaskedArray
        Concatenated array of data across of cubesphere faces
    """

    assert len(tiles) == 6, "Six cubesphere tiles must be provided."

    return np.ma.concatenate(
        (
            tiles[0].variables[var][:],
            tiles[1].variables[var][:],
            tiles[2].variables[var][:],
            tiles[3].variables[var][:],
            tiles[4].variables[var][:],
            tiles[5].variables[var][:],
        ),
        axis=-1,
    )


def write_sqlite_data(
    sqlfile, varname, fyear, varmean=None, varsum=None, component=None
):
    """Writes data to sqlite file

    Parameters
    ----------
    sqlfile : str, path-like
        Path to output sqlite file
    varname : str
        Variable name
    fyear : str
        Year being processed
    varmean : float, optional
        Mean of the data, by default None
    varsum : float, optional
        Sum of variable of the data, by default None
    component : str, optional
        Model component, by default None
    """

    missing_value = -1.0e20

    # check if result is a nan and replace with a defined missing value
    if varmean is not None:
        if math.isnan(float(varmean)):
            warnings.warn(
                f"Could not update {sqlfile} variable {varname} with mean={varmean}"
            )
            varmean = missing_value

    if varsum is not None:
        if math.isnan(float(varsum)):
            warnings.warn(
                f"Could not update {sqlfile} variable {varname} with mean={varsum}"
            )
            varsum = missing_value

    conn = sqlite3.connect(sqlfile)
    cur = conn.cursor()
    if component == "land":
        sql = (
            "create table if not exists "
            + varname
            + " (year integer primary key, sum float, avg float)"
        )
    else:
        sql = (
            "create table if not exists "
            + varname
            + " (year integer primary key, value float)"
        )
    cur.execute(sql)
    if component == "land":
        sql = (
            "insert or replace into "
            + varname
            + " values("
            + fyear[:4]
            + ","
            + str(varsum)
            + ","
            + str(varmean)
            + ")"
        )
    else:
        sql = (
            "insert or replace into "
            + varname
            + " values("
            + fyear[:4]
            + ","
            + str(varmean)
            + ")"
        )
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def parse_cell_measures(attr, key):
    """Parse cell measures attribute

    Parameters
    ----------
    attr : str
        Cell measurues attribute string
    key : str
        Variable name key

    Returns
    -------
    str
        Returns truncated cell measures string
    """
    if attr is not None:
        ind = attr.split().index(key + ":") + 1
        return attr.split()[ind]
    return None


def extract_metadata(dset, varname, attr):
    """Obtain a specific variable attribute

    Parameters
    ----------
    dset : netCDF4.Dataset
        Input NetCDF dataset
    varname : str
        Variable name
    attr : str
        Requested attribute

    Returns
    -------
    str
        Variable attribute string
    """
    if attr in dset.variables[varname].__dict__.keys():
        return dset.variables[varname].__dict__[attr]
    return None


def write_metadata(sqlfile, varname, attr, value):
    """Writes dataset metadata to sqlite file

    Parameters
    ----------
    sqlfile : str, path-like
        Path to output sqlite file
    varname : str
        Variable name
    attr : str
        Attribute name
    value : str
        Attribute string
    """
    if value is None:
        value = str("")
    conn = sqlite3.connect(sqlfile)
    cur = conn.cursor()
    sql = (
        "create table if not exists "
        + str(attr)
        + " (var text primary key, value text)"
    )
    cur.execute(sql)
    sql = (
        "insert or replace into "
        + str(attr)
        + ' values("'
        + str(varname)
        + '","'
        + str(value)
        + '")'
    )
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def standard_grid_cell_area(lat, lon, earth_radius=6371.0e3):
    """Calculate grid cell area for a standard grid

    Parameters
    ----------
    lat : numpy.ndarray
        Array of latitude axis
    lon : numpy.ndarray
        Array of longitude axis
    earth_radius : float, optional
        Radius of the Earth, by default 6371.0e3

    Returns
    -------
    numpy.ndarray
        Array of cell areas
    """
    dlat = lat[1] - lat[0]
    dlon = lon[1] - lon[0]
    area = np.empty((len(lat), len(lon)))
    for j, _lat in enumerate(lat):
        for i, _lon in enumerate(lon):
            lon1 = _lon + dlon / 2.0
            lon0 = _lon - dlon / 2.0
            lat1 = _lat + dlat / 2.0
            lat0 = _lat - dlat / 2.0
            area[j, i] = (
                (np.pi / 180.0)
                * earth_radius
                * earth_radius
                * np.abs(np.sin(np.radians(lat0)) - np.sin(np.radians(lat1)))
                * np.abs(lon0 - lon1)
            )
    return area
