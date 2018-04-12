import gmeantools
import netCDF4 as nc
import numpy as np
import sqlite3
import sys

fYear = sys.argv[1]
outdir = sys.argv[2]
label = sys.argv[3]
history = str(sys.argv[4]).split(',')

gs_tiles = []
for tx in range(1,7): gs_tiles.append(gmeantools.ncopen(fYear + '.grid_spec.tile'+str(tx)+'.nc'))

geoLat = gmeantools.cube_sphere_aggregate('grid_latt',gs_tiles)
geoLon = gmeantools.cube_sphere_aggregate('grid_lont',gs_tiles)
cellArea = gmeantools.cube_sphere_aggregate('area',gs_tiles)

for atmosFile in history:
    data_tiles = []
    for tx in range(1,7): data_tiles.append(gmeantools.ncopen(fYear + '.'+atmosFile+'.tile'+str(tx)+'.nc'))
    for varName in data_tiles[0].variables.keys():
      if (len(data_tiles[0].variables[varName].shape) == 3):
        var = gmeantools.cube_sphere_aggregate(varName,data_tiles)
        var = np.ma.average(var,axis=0,weights=data_tiles[0].variables['average_DT'][:])
        for reg in ['global','tropics','nh','sh']:
          result, areaSum = gmeantools.area_mean(var,cellArea,geoLat,geoLon,region=reg)
          gmeantools.write_sqlite_data(outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db',varName,fYear[:4],result)
          gmeantools.write_sqlite_data(outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db','area',fYear[:4],areaSum)

exit()
