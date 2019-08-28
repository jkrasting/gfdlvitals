import numpy as np
import multiprocessing

import gfdlvitals.util.gmeantools as gmeantools

__all__ = ['process_var','average']

def process_var(varName):
     units     = gmeantools.extract_metadata(data_tiles[0],varName,'units')
     long_name = gmeantools.extract_metadata(data_tiles[0],varName,'long_name')
     if (len(data_tiles[0].variables[varName].shape) == 3):
       var = gmeantools.cube_sphere_aggregate(varName,data_tiles)
       var = np.ma.average(var,axis=0,
           weights=data_tiles[0].variables['average_DT'][:])
       for reg in ['global','tropics','nh','sh']:
         result, areaSum = gmeantools.area_mean(var,cellArea,
             geoLat,geoLon,region=reg)
         sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db'
         gmeantools.write_metadata(sqlfile,varName,'units',units)
         gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
         gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
         gmeantools.write_sqlite_data(sqlfile,'area',fYear[:4],areaSum)


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
    global cellArea

    geoLat = gmeantools.cube_sphere_aggregate('grid_latt',gs_tiles)
    geoLon = gmeantools.cube_sphere_aggregate('grid_lont',gs_tiles)
    cellArea = gmeantools.cube_sphere_aggregate('area',gs_tiles)

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,data_tiles[0].variables.keys())
