from gfdlvitals.util import gmeantools
import numpy as np
import sys

#sys.path.append('/nbhome/ogrp/warsaw_201710_MOM6_2017.10.19/'+
#    'OM4p25_IAF_baseline/mom6/tools/analysis/')

from . import m6toolbox

__all__ = ['MOM6']

def MOM6(vhFile,f_ocean_hgrid,f_topog,fYear,outdir,label):
    if 'vmo' in vhFile.variables.keys():
        vh  = (vhFile.variables['vmo'][0].filled(0)) * 1.e-9
        zt  = vhFile.variables['z_i'][:]
        yq  = vhFile.variables['yq'][:]
    else:
        print('amoc.py FATAL: vmo variable not present in ocean_annual_z.nc')
        exit(0)
    
    #-- Get grid info from gridspec file
    x = f_ocean_hgrid.variables['x'][1::2,1::2]
    y = f_ocean_hgrid.variables['y'][1::2,1::2]
    depth = f_topog.variables['depth'][:]
    code = m6toolbox.genBasinMasks(x, y, depth)
    
    #-- Define atlantic/arctic mask
    atlmask = np.where(np.logical_or(code==2,code==4),1.,0.)
    
    #-- Compute psi
    psi = m6toolbox.MOCpsi(vh,vmsk=atlmask)
    maxsfn = np.max(psi[np.logical_and(zt>500,zt<2500)][:,np.greater_equal(yq,20)])
    print("  AMOC = "+str(maxsfn))
    
    #-- Write to sqlite
    gmeantools.write_sqlite_data(outdir+'/'+fYear+'.globalAve'+label+'.db',
        'amoc_vh',fYear[:4],maxsfn)
