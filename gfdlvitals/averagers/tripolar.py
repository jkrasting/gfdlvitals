import numpy as np
import multiprocessing

import gfdlvitals.util.gmeantools as gmeantools

__all__ = ['process_var','average']

def process_var(varName):
    units     = gmeantools.extract_metadata(fdata,varName,'units')
    long_name = gmeantools.extract_metadata(fdata,varName,'long_name')
    ndims = len(fdata.variables[varName].shape)
    if ndims >= 3:
        if ndims == 3:
          dims = fdata.variables[varName].dimensions
          if (dims[-2] == 'yh' and dims[-1] == 'xh'):
            var = fdata.variables[varName][:]
          else:
            return
        elif (ndims == 4) and (varName[0:9] == 'tot_layer'):
          var = fdata.variables[varName][:]
          var = np.ma.sum(var,axis=1)
        else:
          return
        var = np.ma.average(var,axis=0,weights=fdata.variables['average_DT'][:])
        for reg in ['global','tropics','nh','sh']:
          result, areaSum = gmeantools.area_mean(var,cellArea,geoLat,geoLon,region=reg)
          sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db'
          gmeantools.write_metadata(sqlfile,varName,'units',units)
          gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
          gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
          gmeantools.write_sqlite_data(sqlfile,'area',fYear[:4],areaSum)

def average(f1,f2,year,out,lab):
    global fgs
    global fdata
    global fYear
    global outdir
    global label
 
    fgs = f1
    fdata = f2
    fYear = year
    outdir = out
    label = lab

    # geometry
    global geoLon
    global geoLat
    global cellArea

    if 'geolat' in fgs.variables.keys():
        geoLat   = fgs.variables['geolat'][:]
    elif 'geolat_t' in fgs.variables.keys():
        geoLat   = fgs.variables['geolat_t'][:]
    else:
        raise ValueError('Unable to determine geolat.')
        exit()

    if 'geolon' in fgs.variables.keys():
        geoLon   = fgs.variables['geolon'][:]
    elif 'geolat_t' in fgs.variables.keys():
        geoLon   = fgs.variables['geolon_t'][:]
    else:
        raise ValueError('Unable to determine geolon.')
        exit()

    if 'areacello' in fgs.variables.keys():
        cellArea = fgs.variables['areacello'][:]
    elif 'area_t' in fgs.variables.keys():
        cellArea = fgs.variables['area_t'][:]
    else:
        raise ValueError('Unable to determine ocean cell area.')
        exit()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,fdata.variables.keys())
