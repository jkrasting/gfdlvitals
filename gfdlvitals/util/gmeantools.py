import netCDF4 as nc
import numpy as np
import os
import pickle
import sqlite3
import random
import time

__all__ = ['getWebsiteVariablesDic',
    'ncopen',
    'mask_latitude_bands',
    'area_mean',
    'legacy_area_mean',
    'cube_sphere_aggregate',
    'write_sqlite_data',
    'parse_cell_measures',
    'extract_metadata',
    'write_metadata']

def getWebsiteVariablesDic():
    return pickle.load(open('/home/fms/local/opt/fre-analysis/test/eem/code/cm4_web_analysis/'+\
                            'etc/LM3_variable_dictionary.pkl', 'rb'))

def ncopen(file,action='exit'):
    if os.path.exists(file):
      return nc.Dataset(file)
    else:
      print('WARNING: Unable to open file '+file)
      if action == 'exit':
        exit(0)
      else:
        return None

def mask_latitude_bands(var,cellArea,geoLat,geoLon,region=None):
    if (region == 'tropics'):
      var = np.ma.masked_where(np.logical_or(geoLat < -30., geoLat > 30.),var)
      cellArea = np.ma.masked_where(np.logical_or(geoLat < -30., geoLat > 30.),cellArea)
    elif (region == 'nh'):
      var = np.ma.masked_where(np.less_equal(geoLat,30.),var)
      cellArea  = np.ma.masked_where(np.less_equal(geoLat,30.),cellArea)
    elif (region == 'sh'):
      var  = np.ma.masked_where(np.greater_equal(geoLat,-30.),var)
      cellArea  = np.ma.masked_where(np.greater_equal(geoLat,-30.),cellArea)
    elif (region == 'global'):
      var  = var
      cellArea = cellArea
    return var, cellArea

def area_mean(var,cellArea,geoLat,geoLon,region='global',varName=None,cell_depth=None, component=None):
    if cell_depth is not None:
      if var.shape[0] == cell_depth.shape[0]:
        cellArea = np.tile(cellArea[None,:], (cell_depth.shape[0],1,1))
        geoLat = np.tile(geoLat[None,:], (cell_depth.shape[0],1,1))
        geoLon = np.tile(geoLon[None,:], (cell_depth.shape[0],1,1))
      else:
        print('Warning: inconsisent dimensions between varName and the cell depth axis.', \
               var.shape[0], cell_depth.shape[0])
        null_result = np.ma.masked_where(True,0.)
        return null_result, null_result
    cellArea = np.ma.array(cellArea)
    cellArea.mask = var.mask
    var, cellArea = mask_latitude_bands(var,cellArea,geoLat,geoLon,region=region)
    if cell_depth is not None:
      summed = np.ma.sum(var * cellArea * np.tile(cell_depth[:,None,None], (1,var.shape[1],var.shape[2])))
      var = np.ma.average(var,axis=0,weights=cell_depth)
      res = np.ma.sum(var*cellArea)/cellArea.sum()
      return res, summed.sum()
    else:
      res = np.ma.sum(var*cellArea)/cellArea.sum()
      return res, cellArea.sum()

def legacy_area_mean(var,cellArea,geoLat,geoLon,cellFrac=None,soilFrac=None,region='global',varName=None,cell_depth=None, component=None):
    # Land-specific modifications
    if component == 'land':
        moduleDic = getWebsiteVariablesDic()
        # Read dictionary of keys
        if (varName in moduleDic.keys()):
          module = moduleDic[varName]
        elif (varName.lower() in moduleDic.keys()):
          module = moduleDic[varName.lower()]
        else:
          module = ''
        # Create a weighting factor
        if module == 'vegn':
          cellArea = cellArea*cellFrac*soilFrac
        else:
          cellArea = cellArea*cellFrac
        # Create a 3-D mask if needed
        if cell_depth is not None:
         if var.shape[0] == cell_depth.shape[0]:
           cellArea = np.tile(cellArea[None,:], (cell_depth.shape[0],1,1))
           geoLat = np.tile(geoLat[None,:], (cell_depth.shape[0],1,1))
           geoLon = np.tile(geoLon[None,:], (cell_depth.shape[0],1,1))
         else:
           print('Warning: inconsisent dimensions between varName and the cell depth axis.', \
                 var.shape[0], cell_depth.shape[0])
           null_result = np.ma.masked_where(True,0.)
           return null_result, null_result
        # Apply data mask to weighting mask
        cellArea.mask = var.mask
    var, cellArea = mask_latitude_bands(var,cellArea,geoLat,geoLon,region=region)
    #-- Land depth averaging and summation
    if cell_depth is not None:
      summed = np.ma.sum(var * cellArea * np.tile(cell_depth[:,None,None], (1,var.shape[1],var.shape[2])))
      var = np.ma.average(var,axis=0,weights=cell_depth)
      res = np.ma.sum(var*cellArea)/cellArea.sum()
      return res, summed
    else:
      res = np.ma.sum(var*cellArea)/cellArea.sum()
      summed = np.ma.sum(var*cellArea)
      return res, summed


def cube_sphere_aggregate(var,tiles):
    return np.ma.concatenate((tiles[0].variables[var][:], tiles[1].variables[var][:],\
                              tiles[2].variables[var][:], tiles[3].variables[var][:],\
                              tiles[4].variables[var][:], tiles[5].variables[var][:]),axis=-1)

def write_sqlite_data(sqlfile,varName,fYear,varmean=None,varsum=None,component=None):
    if component == 'land':
      sql1 = 'create table if not exists '+varName+' (year integer primary key, sum float, avg float)'
      sql2 = 'insert or replace into '+varName+' values('+fYear[:4]+','+str(varsum)+','+str(varmean)+')'
    else:
      sql1 = 'create table if not exists '+varName+' (year integer primary key, value float)'
      sql2 = 'insert or replace into '+varName+' values('+fYear[:4]+','+str(varmean)+')'
    #time.sleep(random.random())
    conn = sqlite3.connect(sqlfile)
    c = conn.cursor()
    sqlres = c.execute(sql1)
    sqlres = c.execute(sql2)
    c.close()
    conn.commit()
    conn.close()

def parse_cell_measures(attr,key):
    if attr is not None:
        ind = attr.split().index(key+':')+1
        return attr.split()[ind]
    else:
        return None

def extract_metadata(f,varName,attr):
    if attr in f.variables[varName].__dict__.keys(): 
        return f.variables[varName].__dict__[attr]
    else:
        return None

def write_metadata(sqlfile,varName,attr,value):
    if value is None:
        value = str('')
    sql1 = 'create table if not exists '+str(attr)+' (var text primary key, value text)'
    sql2 = 'insert or replace into '+str(attr)+' values("'+str(varName)+'","'+str(value)+'")'
    #time.sleep(random.random())
    conn = sqlite3.connect(sqlfile)
    c = conn.cursor()
    sqlres = c.execute(sql1)
    sqlres = c.execute(sql2)
    c.close()
    conn.commit()
    conn.close()

def standard_grid_cell_area(lat,lon,rE=6371.e3):
    dLat = lat[1] - lat[0]
    dLon = lon[1] - lon[0]
    area = np.empty((len(lat),len(lon)))
    for j in range(0,len(lat)):
        for i in range(0,len(lon)):
            lon1 = lon[i] + dLon/2.
            lon0 = lon[i] - dLon/2.
            lat1 = lat[j] + dLat/2.
            lat0 = lat[j] - dLat/2.
            area[j,i] = (np.pi/180.) * rE * rE * \
                        np.abs(np.sin(np.radians(lat0))-np.sin(np.radians(lat1))) * \
                        np.abs(lon0-lon1)
    return area
