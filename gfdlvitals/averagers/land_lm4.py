import numpy as np
import multiprocessing
import re

import gfdlvitals.util.gmeantools as gmeantools

__all__ = ['process_var','average']

def process_var(varName):
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
          result, areaSum = gmeantools.area_mean(var,area_types[area_measure],
              geoLat,geoLon,region=reg)
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
            result, volumeSum = gmeantools.area_mean(var,area_types[area_measure],
                geoLat,geoLon,region=reg,cellDepth=cellDepth)
            sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db' 
            gmeantools.write_metadata(sqlfile,varName,'units',units)
            gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
            gmeantools.write_metadata(sqlfile,varName,'cell_measure',area_measure.replace('area','volume'))
            gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
            gmeantools.write_sqlite_data(sqlfile,area_measure.replace('area','volume'),fYear[:4],volumeSum)


def average(gs_tl,da_tl,year,out,lab):
    global gs_tiles
    global data_tiles
    global fYear
    global outdir
    global label

    gs_tiles = gs_tl
    data_tiles = da_tl
    fYear = year
    outdir = out
    label = lab

    global geoLon
    global geoLat

    for f in [ data_tiles, gs_tiles ]:
      if 'geolat_t' in f[0].variables:
        geoLat = gmeantools.cube_sphere_aggregate('geolat_t',data_tiles)
        geoLon = gmeantools.cube_sphere_aggregate('geolon_t',data_tiles)
        break

    global area_types

    area_types = {}
    for f in [ data_tiles , gs_tiles ]:
      for v in sorted(f[0].variables):
        if re.match(r'.*_area',v) or re.match(r'area.*',v):
          # for now, skip the area variables that depend on time
          timedependent=False
          for d in f[0].variables[v].dimensions:
            timedependent=timedependent or f[0].dimensions[d].isunlimited()
          if not timedependent:
            if v not in area_types.keys():
              area_types[v] = gmeantools.cube_sphere_aggregate(v,f)

    global cellDepth

    depth = data_tiles[0].variables['zhalf_soil'][:]
    cellDepth = []
    for i in range(1,len(depth)):
      thickness = round((depth[i] - depth[i-1]),2)
      cellDepth.append(thickness)
    cellDepth = np.array(cellDepth)

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,data_tiles[0].variables.keys())
