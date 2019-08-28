from . import gmeantools

__all__ = ['MOM6']

def MOM6(fdata,fYear,outdir):

    ignoreList = ['time_bounds', 'time_bnds', 'average_T2', \
                  'average_T1', 'average_DT']

    varDict = fdata.variables.keys()
    varDict = list(set(varDict) - set(ignoreList))

    for varName in varDict:
        if len(fdata.variables[varName].shape) == 2:
            units     = gmeantools.extract_metadata(fdata,varName,'units')
            long_name = gmeantools.extract_metadata(fdata,varName,'long_name')
            result = fdata.variables[varName][0,0]
            sqlfile = outdir+'/'+fYear+'.globalAveOcean.db'
            gmeantools.write_metadata(sqlfile,varName,'units',units)
            gmeantools.write_metadata(sqlfile,varName,'long_name',long_name)
            gmeantools.write_sqlite_data(sqlfile,varName,fYear[:4],result)
