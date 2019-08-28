import numpy as np
import multiprocessing

import gfdlvitals.util.gmeantools as gmeantools

__all__ = ['process_var','average']

def process_var(varName):
    varshape = fdata.variables[varName].shape
    if (len(varshape) >= 3):
        var = fdata[varName][:]
        var = np.ma.average(var,axis=0,weights=fdata['average_DT'][:])

    if (len(varshape) == 3):
        for reg in ['global','tropics','nh','sh']:
            sqlfile = outdir+'/'+fYear+'.'+reg+'Ave'+label+'.db'
            avg, summed = gmeantools.legacy_area_mean(var,cellArea,geoLat, \
                geoLon,cellFrac=cellFrac,soilFrac=soilFrac,region=reg, \
                varName=varName,component='land')
            if not hasattr(avg,'mask'):
                gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4], \
                    varmean=avg,varsum=summed,component='land')

def average(f1,f2,year,out,lab):
    global fs
    global fdata
    global fYear
    global outdir
    global label
 
    fs = f1
    fdata = f2
    fYear = year
    outdir = out
    label = lab

    # geometry
    global geoLon
    global geoLat

    lat = fdata['lat'][:]
    lon = fdata['lon'][:]
    geoLon, geoLat = np.meshgrid(lon,lat)

    # land areas and fractions
    global cellArea
    global cellFrac
    global soilArea
    global soilFrac

    cellArea = fs['land_area'][:]
    cellFrac = fs['land_frac'] [:]

    if 'soil_area' in fs.variables.keys():
        soilArea = fs['soil_area'][0]
    elif 'soil_area' in fdata.variables.keys():
        soilArea = fdata['soil_area'][0]
    else:
        raise ValueError('Unable to locate soil area field.')
    soilFrac = np.ma.array(soilArea/(cellArea*cellFrac))

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,fdata.variables.keys())
