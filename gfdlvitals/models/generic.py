import tarfile

from gfdlvitals import averagers
from gfdlvitals import diags
from gfdlvitals.util import extract_ocean_scalar
from gfdlvitals.util.netcdf import extract_from_tar

__all__ = ['routines']

def routines(args,infile):
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
    #-- data tiles
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


    #-- Aerosols
    label = 'AtmosAer'
    modules = ['atmos_month_aer']
    #-- open gridspec tiles
    gs_tiles = []
    for tx in range(1,7):
        gs_tiles.append(extract_from_tar(tar,
            modifier+fYear + '.grid_spec.tile'+str(tx)+'.nc'))
    #-- data tiles
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


    #-- Aerosols (CMIP)
    label = 'AeroCMIP'
    modules = ['aerosol_month_cmip']
    #-- open gridspec tiles
    gs_tiles = []
    for tx in range(1,7):
        gs_tiles.append(extract_from_tar(tar,
            modifier+fYear + '.grid_spec.tile'+str(tx)+'.nc'))
    #-- data tiles
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


    #-- Land
    label = 'Land'
    modules = ['land_month']
    #-- open gridspec tiles
    gs_tiles = []
    for tx in range(1,7):
        gs_tiles.append(extract_from_tar(tar,
            modifier+fYear + '.land_static.tile'+str(tx)+'.nc'))
    #-- data tiles
    for module in modules:
        fname = modifier+fYear + '.'+module+'.tile1.nc'
        if fname in members:
            data_tiles = []
            for tx in range(1,7): 
                data_tiles.append(extract_from_tar(tar,
                    modifier+fYear + '.'+module+'.tile'+str(tx)+'.nc'))
            print(fname)
            averagers.land_lm4.average(gs_tiles,data_tiles,fYear,'./',label)
            for ds in data_tiles:
                ds.close()


    #-- Ice
    label = 'Ice'
    modules = ['ice_month']
    if modifier+fYear+'.ice_static.nc' in members:
        fgs = extract_from_tar(tar,modifier+fYear+'.ice_static.nc')
    else:
        fgs = extract_from_tar(tar,modifier+fYear+'.ice_month.nc')
    for module in modules:
        fname = modifier+fYear+'.'+module+'.nc'
        if fname in members:
            fdata = extract_from_tar(tar,fname)
            print(fname)
            averagers.ice.average(fgs,fdata,fYear,'./',label)
            fdata.close()
    fgs.close()


    #-- COBALT
    label = 'COBALT'
    modules = ['ocean_cobalt_sfc','ocean_cobalt_misc',
               'ocean_cobalt_tracers_year','ocean_cobalt_tracers_int']
    if modifier+fYear+'.ocean_static.nc' in members:
        fgs = extract_from_tar(tar,modifier+fYear+'.ocean_static.nc')
    else:
        fgs = extract_from_tar(tar,modifier+fYear+'.ocean_month.nc')
    for module in modules:
        fname = modifier+fYear+'.'+module+'.nc'
        if fname in members:
            fdata = extract_from_tar(tar,fname)
            print(fname)
            averagers.tripolar.average(fgs,fdata,fYear,'./',label)
            fdata.close()
    fgs.close()


    #-- BLING
    label = 'BLING'
    modules = ['ocean_bling','ocean_bling_cmip6_omip_2d',
               'ocean_bling_cmip6_omip_rates_year_z',
               'ocean_bling_cmip6_omip_sfc',
               'ocean_bling_cmip6_omip_tracers_month_z',
               'ocean_bling_cmip6_omip_tracers_year_z']
    if modifier+fYear+'.ocean_static.nc' in members:
        fgs = extract_from_tar(tar,modifier+fYear+'.ocean_static.nc')
    else:
        fgs = extract_from_tar(tar,modifier+fYear+'.ocean_month.nc')
    for module in modules:
        fname = modifier+fYear+'.'+module+'.nc'
        if fname in members:
            fdata = extract_from_tar(tar,fname)
            print(fname)
            averagers.tripolar.average(fgs,fdata,fYear,'./',label)
            fdata.close()
    fgs.close()

    
    #-- Ocean
    label = 'Ocean'
    fname = modifier + fYear + '.ocean_scalar_annual.nc'
    if fname in members:
        print(fname)
        fdata = extract_from_tar(tar,fname)
        extract_ocean_scalar.MOM6(fdata,fYear,'./')
        fdata.close()


    #-- AMOC
    label = 'Ocean'
    if args.gridspec is not None:
        gs_tar = tarfile.open(args.gridspec)
        _contents = gs_tar.getnames()

        hgrid_file = [x for x in _contents if 'ocean_hgrid' in x]
        if len(hgrid_file) == 1:
            hgrid_file = hgrid_file[0]
        elif len(hgrid_file) > 1:
            print('Multiple ocean_hgrid files found ... skipping AMOC')
        else:
            print('No ocean_hgrid file found ... skipping AMOC')

        topog_file = [x for x in _contents if 'ocean_topog' in x]
        if len(topog_file) == 1:
            topog_file = topog_file[0]
        elif len(topog_file) > 1:
            print('Multiple ocean_topog files found ... skipping AMOC')
        else:
            print('No ocean_topog file found ... skipping AMOC')

        ocean_hgrid = extract_from_tar(gs_tar,hgrid_file)
        topog = extract_from_tar(gs_tar,topog_file)
        fname = modifier + fYear + '.ocean_annual_z.nc'
        if fname in members:
            vhFile = extract_from_tar(tar,fname)
            diags.amoc.MOM6(vhFile,ocean_hgrid,topog,fYear,'./',label)
            ocean_hgrid.close()
            topog.close()
            vhFile.close()
        gs_tar.close()

    #-- Close out the tarfile handle
    tar.close()
