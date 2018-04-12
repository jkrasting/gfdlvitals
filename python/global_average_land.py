import gmeantools
import numpy as np
import netCDF4 as nc
import pickle
import re
import sqlite3
import sys
import urllib2

fYear = sys.argv[1]
outdir = sys.argv[2]
label = sys.argv[3]
history = sys.argv[4]

gs_tiles = []
for tx in range(1,7): gs_tiles.append(gmeantools.ncopen(fYear + '.land_static.tile'+str(tx)+'.nc'))

data_tiles = []
for tx in range(1,7): data_tiles.append(gmeantools.ncopen(fYear + '.'+history+'.tile'+str(tx)+'.nc'))

geoLat = gmeantools.cube_sphere_aggregate('geolat_t',gs_tiles)
geoLon = gmeantools.cube_sphere_aggregate('geolon_t',gs_tiles)
cellArea = gmeantools.cube_sphere_aggregate('land_area',gs_tiles)
cellFrac = gmeantools.cube_sphere_aggregate('land_frac',gs_tiles)
soilArea = gmeantools.cube_sphere_aggregate('soil_area',gs_tiles)
soilFrac = np.ma.array(soilArea/(cellArea*cellFrac))

depth = data_tiles[0].variables['zhalf_soil'][:]
cellDepth = []
for i in range(1,len(depth)):
  thickness = round((depth[i] - depth[i-1]),2)
  cellDepth.append(thickness)
cellDepth = np.array(cellDepth)

for varName in data_tiles[0].variables.keys():
  varshape = data_tiles[0].variables[varName].shape
  if (len(varshape) >= 3):
    var = gmeantools.cube_sphere_aggregate(varName,data_tiles)
    var = np.ma.average(var,axis=0,weights=data_tiles[0].variables['average_DT'][:])

    if (len(varshape) == 3):
      for reg in ['global','tropics','nh','sh']:
        avg, wgt = gmeantools.area_mean(var,cellArea,geoLat,geoLon,cellFrac=cellFrac,soilFrac=soilFrac,\
                                       region=reg,varName=varName,component='land')
        if not hasattr(avg,'mask'):
          gmeantools.write_sqlite_data(outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db',varName,fYear[:4],\
                                       varmean=avg,varsum=avg*wgt,component='land')

    elif (len(varshape) == 4):
      if varshape[1] == cellDepth.shape[0]:
        for reg in ['global','tropics','nh','sh']:
          avg, summed = gmeantools.area_mean(var,cellArea,geoLat,geoLon,cellFrac=cellFrac,soilFrac=soilFrac,\
                                             region=reg,varName=varName,cellDepth=cellDepth,component='land')
          gmeantools.write_sqlite_data(outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db',varName,fYear[:4],\
                                       varmean=avg,varsum=summed,component='land')

exit()
