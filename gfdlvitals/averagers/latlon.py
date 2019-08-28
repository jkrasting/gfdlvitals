import numpy as np
import multiprocessing

import gfdlvitals.util.gmeantools as gmeantools

__all__ = ['process_var','average']

def process_var(varName):
      units     = gmeantools.extract_metadata(f,varName,'units')
      long_name = gmeantools.extract_metadata(f,varName,'long_name')
      if (len(f.variables[varName].shape) == 3):
          var = f.variables[varName][:]
          var = np.ma.average(var,axis=0,weights=f.variables['average_DT'][:])
          for reg in ['global','tropics','nh','sh']:
              result, areaSum = gmeantools.area_mean(var,cellArea,
                                    geoLat,geoLon,region=reg)
              sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db'
              gmeantools.write_metadata(sqlfile,varName,'units',units)
              gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
              gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
              gmeantools.write_sqlite_data(sqlfile,'area',fYear[:4],areaSum)


def average(f1,f2,year,out,lab):
    global fs
    global f
    global fYear
    global outdir
    global label

    fs = f1
    f = f2
    fYear = year
    outdir = out
    label = lab

    # geometry
    global geoLon
    global geoLat
    global cellArea

    lat = fs.variables['lat'][:]
    lon = fs.variables['lon'][:]
    geoLat = np.tile(lat[:,None],(1,lon.shape[0]))
    geoLon = np.tile(lon[None,:],(lat.shape[0],1))
    cellArea = gmeantools.standard_grid_cell_area(lat,lon)

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,f.variables.keys())
