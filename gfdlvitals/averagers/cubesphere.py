import numpy as np
import netCDF4
import multiprocessing

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ['process_var','average']

def process_var(variables):
     data_tiles = [nctools.in_mem_nc(x) for x in variables.data_tiles]
     units     = gmeantools.extract_metadata(data_tiles[0],variables.varname,'units')
     long_name = gmeantools.extract_metadata(data_tiles[0],variables.varname,'long_name')
     if (len(data_tiles[0].variables[variables.varname].shape) == 3):
       var = gmeantools.cube_sphere_aggregate(variables.varname,data_tiles)
       var = np.ma.average(var,axis=0,
           weights=data_tiles[0].variables['average_DT'][:])
       for reg in ['global','tropics','nh','sh']:
         result, areaSum = gmeantools.area_mean(var,variables.cellArea,
             variables.geoLat,variables.geoLon,region=reg)
         sqlfile = variables.outdir+'/'+variables.fYear+'.'+reg+'Ave'+variables.label+'.db'
         gmeantools.write_metadata(sqlfile,variables.varname,'units',units)
         gmeantools.write_metadata(sqlfile,variables.varname,'long_name',long_name)
         gmeantools.write_sqlite_data(sqlfile,variables.varname,variables.fYear[:4],result)
         gmeantools.write_sqlite_data(sqlfile,'area',variables.fYear[:4],areaSum)
     [x.close() for x in data_tiles]
     

class rich_variable:
    def __init__(self,varname,gs_tiles,data_tiles,fYear,outdir,label,geoLat,geoLon,cellArea):
        self.varname = varname
        self.gs_tiles = gs_tiles
        self.data_tiles = data_tiles
        self.fYear = fYear
        self.outdir = outdir
        self.label = label
        self.geoLat = geoLat
        self.geoLon = geoLon
        self.cellArea = cellArea

def average(gs_tl,da_tl,year,out,lab):
    gs_tiles = [nctools.in_mem_nc(x) for x in gs_tl]

    geoLat = gmeantools.cube_sphere_aggregate('grid_latt',gs_tiles)
    geoLon = gmeantools.cube_sphere_aggregate('grid_lont',gs_tiles)
    cellArea = gmeantools.cube_sphere_aggregate('area',gs_tiles)

    [x.close() for x in gs_tiles]

    variables = list(nctools.in_mem_nc(da_tl[0]).variables.keys())
    variables = [rich_variable(x,gs_tl,da_tl,year,out,lab,geoLat,geoLon,cellArea) for x in variables]

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,variables)
