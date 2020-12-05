import numpy as np
import netCDF4
import multiprocessing

import gfdlvitals.util.gmeantools as gmeantools
import gfdlvitals.util.netcdf as nctools

__all__ = ['process_var','average']

def process_var(variable):
    fdata = nctools.in_mem_nc(variable.fdata)
    if fdata.variables[variable.varname].shape == variable.cellArea.shape:
      units     = gmeantools.extract_metadata(fdata,variable.varname,'units')
      long_name = gmeantools.extract_metadata(fdata,variable.varname,'long_name')
      data = fdata.variables[variable.varname][:]
      for reg in ['global','nh','sh']:
        sqlite_out = variable.outdir+'/'+variable.fYear+'.'+reg+'Ave'+variable.label+'.db'
        _v, _area = gmeantools.mask_latitude_bands(data,variable.cellArea,variable.geoLat,variable.geoLon,region=reg)
        _v = np.ma.sum((_v*_area),axis=(-1,-2))/np.ma.sum(_area,axis=(-1,-2))
        gmeantools.write_metadata(sqlite_out,variable.varname,'units',units)
        gmeantools.write_metadata(sqlite_out,variable.varname,'long_name',long_name)
        gmeantools.write_sqlite_data(sqlite_out,variable.varname+'_mean',variable.fYear[:4],np.ma.average(_v,axis=0,weights=variable.average_DT))
        gmeantools.write_sqlite_data(sqlite_out,variable.varname+'_max', variable.fYear[:4],np.ma.max(_v))
        gmeantools.write_sqlite_data(sqlite_out,variable.varname+'_min', variable.fYear[:4],np.ma.min(_v))
    fdata.close()

class rich_variable:
    def __init__(self,varname,fgs,fdata,fYear,outdir,label,geoLat,geoLon,cellArea,average_DT):
        self.varname = varname
        self.fgs = fgs
        self.fdata = fdata
        self.fYear = fYear
        self.outdir = outdir
        self.label = label
        self.geoLat = geoLat
        self.geoLon = geoLon
        self.cellArea = cellArea
        self.average_DT = average_DT

def average(f1,f2,year,out,lab):
    fgs = nctools.in_mem_nc(f1)
    fdata = nctools.in_mem_nc(f2)

    geoLon = fgs.variables['GEOLON'][:]
    geoLat = fgs.variables['GEOLAT'][:]
 
    average_DT = fdata.variables['average_DT'][:]
    
    if 'CELL_AREA' in fgs.variables.keys():
      rE = 6371.0e3  # Radius of the Earth in 'm'
      cellArea = fgs.variables['CELL_AREA'][:] * (4.*np.pi*(rE**2))
    elif 'area' in fgs.variables.keys():
      cellArea = fgs.variables['area'][:]
    else:
      print('FATAL: unable to determine cell area used in ice model')
    
    if 'siconc' in fdata.variables.keys():
      concentration = fdata.variables['siconc'][:]
    elif 'CN' in fdata.variables.keys():
      concentration = np.ma.sum(fdata.variables['CN'][:],axis=-3)
    else:
      print('FATAL: unable to determine ice concentration')
    
    geoLat = np.tile(geoLat[None,:], (concentration.shape[0],1,1))
    geoLon = np.tile(geoLon[None,:], (concentration.shape[0],1,1))
    cellArea = np.tile(cellArea[None,:], (concentration.shape[0],1,1))
    
    for reg in ['global','nh','sh']:
      sqlite_out = out+'/'+year+'.'+reg+'Ave'+lab+'.db'
      vars = []
      # area and extent in million square km
      _conc, _area = gmeantools.mask_latitude_bands(concentration,cellArea,
                         geoLat,geoLon,region=reg)
      vars.append(('area',(np.ma.sum((_conc * _area),axis=(-1,-2))*1.e-12)))
      vars.append(('extent',(np.ma.sum((np.ma.where(np.greater(_conc,0.15),
                      _area,0.)),axis=(-1,-2))*1.e-12)))
      for v in vars:
        gmeantools.write_sqlite_data(sqlite_out,v[0]+'_mean',year[:4],
            np.ma.average(v[1],weights=average_DT))
        gmeantools.write_sqlite_data(sqlite_out,v[0]+'_max', year[:4],
            np.ma.max(v[1]))
        gmeantools.write_sqlite_data(sqlite_out,v[0]+'_min', year[:4],
            np.ma.min(v[1]))

    variables = list(fdata.variables.keys())
    variables = [rich_variable(x,f1,f2,year,out,lab,geoLat,geoLon,cellArea,average_DT) for x in variables]

    fgs.close()
    fdata.close()

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_var,variables)
