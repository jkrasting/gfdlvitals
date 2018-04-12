import gmeantools
import netCDF4 as nc
import numpy as np
import sqlite3
import sys

fYear = sys.argv[1]
outdir = sys.argv[2]

fdata = gmeantools.ncopen(fYear + '.ocean_scalar_annual.nc')

ignoreList = ['time_bounds', 'time_bnds', 'average_T2', 'average_T1', 'average_DT']
varDict = fdata.variables.keys()
varDict = list(set(varDict) - set(ignoreList))

for varName in varDict:
  if len(fdata.variables[varName].shape) == 2:
    result = fdata.variables[varName][0,0]
    gmeantools.write_sqlite_data(outdir+'/'+fYear+'.globalAveOcean.db',varName,fYear[:4],result)

exit()
