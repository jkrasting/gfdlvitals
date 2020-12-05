import numpy as np
import netCDF4
import multiprocessing
import re

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ['process_var','average']

def process_var(variable):
  data_tiles = [nctools.in_mem_nc(x) for x in variable.data_tiles]

  varshape = data_tiles[0].variables[variable.varname].shape
  units     = gmeantools.extract_metadata(data_tiles[0],variable.varname,'units')
  long_name = gmeantools.extract_metadata(data_tiles[0],variable.varname,'long_name')
  cell_measures = gmeantools.extract_metadata(data_tiles[0],variable.varname,'cell_measures')
  area_measure = gmeantools.parse_cell_measures(cell_measures,'area')
  if (area_measure is not None) and (area_measure != 'area_ntrl'):
    if (len(varshape) >= 3):
      var = gmeantools.cube_sphere_aggregate(variable.varname,data_tiles)
      var = np.ma.average(var,axis=0,weights=data_tiles[0].variables['average_DT'][:])
  
      if (len(varshape) == 3):
        for reg in ['global','tropics','nh','sh']:
          result, areaSum = gmeantools.area_mean(var,variable.area_types[area_measure],
              variable.geoLat,variable.geoLon,region=reg)
          if not hasattr(result,'mask'):
            sqlfile = variable.outdir+'/'+variable.fYear+'.'+reg+'Ave'+variable.label+'.db'
            gmeantools.write_metadata(sqlfile,variable.varname,'units',units)
            gmeantools.write_metadata(sqlfile,variable.varname,'long_name',long_name)
            gmeantools.write_metadata(sqlfile,variable.varname,'cell_measure',area_measure)
            gmeantools.write_sqlite_data(sqlfile,variable.varname,variable.fYear[:4],result)
            gmeantools.write_sqlite_data(sqlfile,area_measure,variable.fYear[:4],areaSum)
  
      elif (len(varshape) == 4):
        if varshape[1] == cellDepth.shape[0]:
          for reg in ['global','tropics','nh','sh']:
            result, volumeSum = gmeantools.area_mean(var,area_types[area_measure],
                variable.geoLat,variable.geoLon,region=reg,cellDepth=variable.cellDepth)
            sqlfile = variable.outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db' 
            gmeantools.write_metadata(sqlfile,variable.varname,'units',units)
            gmeantools.write_metadata(sqlfile,variable.varname,'long_name',long_name)
            gmeantools.write_metadata(sqlfile,variable.varname,'cell_measure',area_measure.replace('area','volume'))
            gmeantools.write_sqlite_data(sqlfile,variable.varname,variable.fYear[:4],result)
            gmeantools.write_sqlite_data(sqlfile,area_measure.replace('area','volume'),variable.fYear[:4],volumeSum)

class rich_variable:
    def __init__(self,varname,gs_tiles,data_tiles,fYear,outdir,label,geoLat,geoLon,area_types,cellDepth):
        self.varname = varname
        self.gs_tiles = gs_tiles
        self.data_tiles = data_tiles
        self.fYear = fYear
        self.outdir = outdir
        self.label = label
        self.geoLat = geoLat
        self.geoLon = geoLon
        self.area_types = area_types
        self.cellDepth = cellDepth


def average(gs_tl,da_tl,year,out,lab):
    gs_tiles = [nctools.in_mem_nc(x) for x in gs_tl]
    data_tiles = [nctools.in_mem_nc(x) for x in da_tl]

    for f in [ data_tiles, gs_tiles ]:
      if 'geolat_t' in f[0].variables:
        geoLat = gmeantools.cube_sphere_aggregate('geolat_t',data_tiles)
        geoLon = gmeantools.cube_sphere_aggregate('geolon_t',data_tiles)
        break

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

    depth = data_tiles[0].variables['zhalf_soil'][:]
    cellDepth = []
    for i in range(1,len(depth)):
      thickness = round((depth[i] - depth[i-1]),2)
      cellDepth.append(thickness)
    cellDepth = np.array(cellDepth)

    variables = list(data_tiles[0].variables.keys())
    variables = [rich_variable(x,gs_tl,da_tl,year,out,lab,geoLat,geoLon,area_types,cellDepth) for x in variables]

    [x.close() for x in gs_tiles]
    [x.close() for x in data_tiles]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,variables)
