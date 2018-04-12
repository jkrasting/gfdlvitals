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
area_types = {}
area_types['land_area'] = gmeantools.cube_sphere_aggregate('land_area',gs_tiles)
area_types['soil_area'] = gmeantools.cube_sphere_aggregate('soil_area',gs_tiles)
area_types['lake_area'] = gmeantools.cube_sphere_aggregate('lake_area',gs_tiles)
area_types['glac_area'] = gmeantools.cube_sphere_aggregate('glac_area',data_tiles)
#area_types['area_ntrl'] = gmeantools.cube_sphere_aggregate('area_ntrl',data_tiles)

depth = data_tiles[0].variables['zhalf_soil'][:]
cellDepth = []
for i in range(1,len(depth)):
  thickness = round((depth[i] - depth[i-1]),2)
  cellDepth.append(thickness)
cellDepth = np.array(cellDepth)

for varName in sorted(data_tiles[0].variables.keys()):
  varshape = data_tiles[0].variables[varName].shape
  units     = gmeantools.extract_metadata(data_tiles[0],varName,'units')
  long_name = gmeantools.extract_metadata(data_tiles[0],varName,'long_name')
  cell_measures = gmeantools.extract_metadata(data_tiles[0],varName,'cell_measures')
  area_measure = gmeantools.parse_cell_measures(cell_measures,'area')
  if (area_measure is not None) and (area_measure != 'area_ntrl'):
    if (len(varshape) >= 3):
      var = gmeantools.cube_sphere_aggregate(varName,data_tiles)
      var = np.ma.average(var,axis=0,weights=data_tiles[0].variables['average_DT'][:])
  
      if (len(varshape) == 3):
        for reg in ['global','tropics','nh','sh']:
          result, areaSum = gmeantools.area_mean(var,area_types[area_measure],geoLat,geoLon,region=reg)
          if not hasattr(result,'mask'):
            sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db'
            gmeantools.write_metadata(sqlfile,varName,'units',units)
            gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
            gmeantools.write_metadata(sqlfile,varName,'cell_measure',area_measure)
            gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
            gmeantools.write_sqlite_data(sqlfile,area_measure,fYear[:4],areaSum)
  
      elif (len(varshape) == 4):
        if varshape[1] == cellDepth.shape[0]:
          for reg in ['global','tropics','nh','sh']:
            result, volumeSum = gmeantools.area_mean(var,area_types[area_measure],geoLat,geoLon,region=reg,cellDepth=cellDepth)
            sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db' 
            gmeantools.write_metadata(sqlfile,varName,'units',units)
            gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
            gmeantools.write_metadata(sqlfile,varName,'cell_measure',area_measure.replace('area','volume'))
            gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
            gmeantools.write_sqlite_data(sqlfile,area_measure.replace('area','volume'),fYear[:4],volumeSum)

exit()
