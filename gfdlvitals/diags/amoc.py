import gmeantools
import netCDF4 as nc
import numpy as np
from scipy.io import netcdf
import sqlite3
import sys
import tarfile

fYear = sys.argv[1]
outdir = sys.argv[2]
gsFile = sys.argv[3]

sys.path.append('/nbhome/ogrp/warsaw_201710_MOM6_2017.10.19/OM4p25_IAF_baseline/mom6/tools/analysis/')

import m6toolbox

#-- Read VMO from file
vhFile = gmeantools.ncopen(fYear+'.ocean_annual_z.nc')
if 'vmo' in vhFile.variables.keys():
    vh  = (vhFile.variables['vmo'][0].filled(0)) * 1.e-9
    zt  = vhFile.variables['z_l'][:]
    yq  = vhFile.variables['yq'][:]
else:
    print('amoc.py FATAL: vmo variable not present in ocean_annual_z.nc')
    exit(0)

#-- Get grid info from gridspec file
if gsFile.split('.')[-1] == 'tar':
    TF = tarfile.open(gsFile,'r')
    member = [m for m in TF.getmembers() if 'ocean_hgrid' in m.name][0]
    nc = netcdf.netcdf_file(TF.extractfile(member),'r')
    x = nc.variables['x'][1::2,1::2]
    y = nc.variables['y'][1::2,1::2]
    member = [m for m in TF.getmembers() if 'topog' in m.name][0]
    nc = netcdf.netcdf_file(TF.extractfile(member),'r')
    depth = nc.variables['depth'][:]
    code = m6toolbox.genBasinMasks(x, y, depth)
else:
    print('amoc.py FATAL: expecting grid_spec to be a tarfile')

#-- Define atlantic/arctic mask
atlmask = np.where(np.logical_or(code==2,code==4),1.,0.)

#-- Compute psi
psi = m6toolbox.MOCpsi(vh,vmsk=atlmask)
maxsfn = np.max(psi[np.logical_and(zt>500,zt<2500)][:,np.greater_equal(yq,20)])
print('AMOC vh = %s' % maxsfn)

gmeantools.write_sqlite_data(outdir+'/'+fYear+'.globalAveOcean.db','amoc_vh',fYear[:4],maxsfn)

exit()
