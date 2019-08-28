import tarfile

from gfdlvitals import averagers
from gfdlvitals.util.netcdf import extract_from_tar

__all__ = ['routines']

def routines(infile):
    #-- Open the tarfile
    tar = tarfile.open(infile)
    members = tar.getnames()
    #-- Set the model year string
    fYear = str(infile.split('/')[-1].split('.')[0])
    print('Processing '+fYear)

    if members[-1][0:2] == "./":
        modifier = "./"
    else:
        modifier = ""

    #-- Atmosphere
    label = 'Atmos'
    modules = ['atmos_month','atmos_co2_month']
    
    #-- open gridspec tiles
    gs_tiles = []
    for tx in range(1,7):
        gs_tiles.append(extract_from_tar(tar,
            modifier+fYear + '.grid_spec.tile'+str(tx)+'.nc'))

    for module in modules:
        fname = modifier+fYear + '.'+module+'.tile1.nc'
        if fname in members:
            data_tiles = []
            for tx in range(1,7): 
                data_tiles.append(extract_from_tar(tar,
                    modifier+fYear + '.'+module+'.tile'+str(tx)+'.nc'))
            print(fname)
            averagers.cubesphere.average(gs_tiles,data_tiles,fYear,'./',label)
            for ds in data_tiles:
                ds.close()

    ### #-- Ocean
    ### label = 'Ocean'
    ### modules = ['ocean_month']
    ### if modifier+fYear+'.ocean_static.nc' in members:
    ###     fgs = extract_from_tar(tar,modifier+fYear+'.ocean_static.nc')
    ### else:
    ###     fgs = extract_from_tar(tar,modifier+fYear+'.ocean_month.nc')
    ### for module in modules:
    ###     fname = modifier+fYear+'.'+module+'.nc'
    ###     if fname in members:
    ###         fdata = extract_from_tar(tar,fname)
    ###         print(fname)
    ###         averagers.tripolar.average(fgs,fdata,fYear,'./',label)
    ###         fdata.close()
    ### fgs.close()

    ### #-- TOPAZ
    ### label = 'TOPAZ'
    ### modules = ['ocean_topaz_fluxes','ocean_topaz_misc','ocean_topaz_sfc_100',\
    ###            'ocean_topaz_tracers_month_z','ocean_topaz_wc_btm']
    ### if modifier+fYear+'.ocean_static.nc' in members:
    ###     fgs = extract_from_tar(tar,modifier+fYear+'.ocean_static.nc')
    ### else:
    ###     fgs = extract_from_tar(tar,modifier+fYear+'.ocean_month.nc')
    ### for module in modules:
    ###     fname = modifier+fYear+'.'+module+'.nc'
    ###     if fname in members:
    ###         fdata = extract_from_tar(tar,fname)
    ###         print(fname)
    ###         averagers.tripolar.average(fgs,fdata,fYear,'./',label)
    ###         fdata.close()
    ### fgs.close()

    ### #-- Ice
    ### label = 'Ice'
    ### modules = ['ice_month']
    ### if modifier+fYear+'.ice_static.nc' in members:
    ###     fgs = extract_from_tar(tar,modifier+fYear+'.ice_static.nc')
    ### else:
    ###     fgs = extract_from_tar(tar,modifier+fYear+'.ice_month.nc')
    ### for module in modules:
    ###     fname = modifier+fYear+'.'+module+'.nc'
    ###     if fname in members:
    ###         fdata = extract_from_tar(tar,fname)
    ###         print(fname)
    ###         averagers.ice.average(fgs,fdata,fYear,'./',label)
    ###         fdata.close()
    ### fgs.close()

    #-- Close out the tarfile handle
    tar.close()
