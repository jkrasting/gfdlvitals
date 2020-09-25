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
        ocean_hgrid = extract_from_tar(gs_tar,'./ocean_hgrid.nc')
        topog = extract_from_tar(gs_tar,'./ocean_topog.nc')
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
