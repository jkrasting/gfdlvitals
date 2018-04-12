import gmeantools
import netCDF4 as nc
import numpy as np
import sqlite3
import sys
import glob

fYear = sys.argv[1]
outdir = sys.argv[2]
label = sys.argv[3]
history = str(sys.argv[4]).split(',')

fgs = gmeantools.ncopen(fYear + '.ocean_static.nc')

geoLat   = fgs.variables['geolat'][:]
geoLon   = fgs.variables['geolon'][:]
cellArea = fgs.variables['areacello'][:]

for oceanFile in history:
  fdata = gmeantools.ncopen(fYear + '.' + oceanFile + '.nc',action=None)
  if fdata is not None:
    for varName in fdata.variables.keys():
      units     = gmeantools.extract_metadata(fdata,varName,'units')
      long_name = gmeantools.extract_metadata(fdata,varName,'long_name')
      ndims = len(fdata.variables[varName].shape)
      if ndims == 3:
        dims = fdata.variables[varName].dimensions
        if (dims[-2] == 'yh' and dims[-1] == 'xh'):
          var = fdata.variables[varName][:]
      elif (ndims == 4) and (varName[0:9] == 'tot_layer'):
        var = fdata.variables[varName][:]
        var = np.ma.sum(var,axis=1)
      else:
        continue
      var = np.ma.average(var,axis=0,weights=fdata.variables['average_DT'][:])
      for reg in ['global','tropics','nh','sh']:
        result, areaSum = gmeantools.area_mean(var,cellArea,geoLat,geoLon,region=reg)
        sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db'
        gmeantools.write_metadata(sqlfile,varName,'units',units)
        gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
        gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
        gmeantools.write_sqlite_data(sqlfile,'area',fYear[:4],areaSum)
  else:
    continue

exit()
