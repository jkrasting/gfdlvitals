""" Extract scalar fields from ocean model output """

from . import gmeantools

__all__ = ["mom6"]


def mom6(fdata, fyear, outdir):
    """Extract MOM6 scalar output and save to sqlite

    Parameters
    ----------
    fdata : netCDF4.Dataset
        Input ocean_scalar.nc file
    fyear : str
        Year being processed
    outdir : str
        Path to output directory
    """

    ignore_list = ["time_bounds", "time_bnds", "average_T2", "average_T1", "average_DT"]

    var_dict = fdata.variables.keys()
    var_dict = list(set(var_dict) - set(ignore_list))

    for varname in var_dict:
        if len(fdata.variables[varname].shape) == 2:
            units = gmeantools.extract_metadata(fdata, varname, "units")
            long_name = gmeantools.extract_metadata(fdata, varname, "long_name")
            result = fdata.variables[varname][0, 0]
            sqlfile = outdir + "/" + fyear + ".globalAveOcean.db"
            gmeantools.write_metadata(sqlfile, varname, "units", units)
            gmeantools.write_metadata(sqlfile, varname, "long_name", long_name)
            gmeantools.write_sqlite_data(sqlfile, varname, fyear[:4], result)
