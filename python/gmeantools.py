import netCDF4 as nc
import numpy as np
import os
import pickle
import sqlite3

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

def area_mean(var,cellArea,geoLat,geoLon,cellFrac=None,soilFrac=None,region='global',varName=None,
              cellDepth=None, component=None):
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
        if cellDepth is not None:
         if var.shape[0] == cellDepth.shape[0]:
           cellArea = np.tile(cellArea[None,:], (cellDepth.shape[0],1,1))
           geoLat = np.tile(geoLat[None,:], (cellDepth.shape[0],1,1))
           geoLon = np.tile(geoLon[None,:], (cellDepth.shape[0],1,1))
         else:
           print('Warning: inconsisent dimensions between varName and the cell depth axis.', \
                 var.shape[0], cellDepth.shape[0])
           null_result = np.ma.masked_where(True,0.)
           return null_result, null_result
        # Apply data mask to weighting mask
        cellArea.mask = var.mask
    var, cellArea = mask_latitude_bands(var,cellArea,geoLat,geoLon,region=region)
    #-- Land depth averaging and summation
    if cellDepth is not None:
      summed = np.ma.sum(var * cellArea * np.tile(cellDepth[:,None,None], (1,var.shape[1],var.shape[2])))
      var = np.ma.average(var,axis=0,weights=cellDepth)
      res = np.ma.sum(var*cellArea)/cellArea.sum()
      return res, summed
    else:
      res = np.ma.sum(var*cellArea)/cellArea.sum()
      return res, cellArea.sum()

def cube_sphere_aggregate(var,tiles):
    return np.ma.concatenate((tiles[0].variables[var][:], tiles[1].variables[var][:],\
                              tiles[2].variables[var][:], tiles[3].variables[var][:],\
                              tiles[4].variables[var][:], tiles[5].variables[var][:]),axis=-1)

def write_sqlite_data(sqlfile,varName,fYear,varmean=None,varsum=None,component=None):
    conn = sqlite3.connect(sqlfile)
    c = conn.cursor()
    if component == 'land':
      sql = 'create table if not exists '+varName+' (year integer primary key, sum float, avg float)'
    else:
      sql = 'create table if not exists '+varName+' (year integer primary key, value float)'
    sqlres = c.execute(sql)
    if component == 'land':
      sql = 'insert or replace into '+varName+' values('+fYear[:4]+','+str(varsum)+','+str(varmean)+')'
    else:
      sql = 'insert or replace into '+varName+' values('+fYear[:4]+','+str(varmean)+')'
    sqlres = c.execute(sql)
    conn.commit()
    c.close()
    conn.close()
