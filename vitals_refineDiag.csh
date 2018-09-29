#------------------------------------------------------------------------------
#  vitals refineDiag.csh
#------------------------------------------------------------------------------

#-- Unload any previous versions of Python and load the system default
module unload python
module unload cdat
module load python

#-- Create a directory to house the sqlite database (if it does not already exist)
set localRoot = `echo $scriptName | rev | cut -f 4-100 -d '/' | rev`
if (! -d ${localRoot}/db) then 
  mkdir -p ${localRoot}/db
endif

#-- Run the averager script
python vitals/python/global_average_cubesphere.py ${oname} ${refineDiagDir} Atmos atmos_month,atmos_co2_month
python vitals/python/global_average_cubesphere.py ${oname} ${refineDiagDir} AtmosAer atmos_month_aer
python vitals/python/global_average_land.py ${oname} ${refineDiagDir} Land land_month
python vitals/python/global_average_ice.py ${oname} ${refineDiagDir} Ice ice_month
python vitals/python/global_average_tripolar.py ${oname} ${refineDiagDir} COBALT ocean_cobalt_sfc,ocean_cobalt_misc,ocean_cobalt_tracers_year,ocean_cobalt_tracers_int
python vitals/python/extract_ocean_scalar.py ${oname} ${refineDiagDir}
python vitals/python/amoc.py ${oname} ${refineDiagDir} ${gridspec}
python vitals/python/global_average_cubesphere.py ${oname} ${refineDiagDir} AeroCMIP aerosol_month_cmip

#-- Copy the database back to its original location
foreach reg (global nh sh tropics)
  foreach component (Atmos AtmosAer Land Ice COBALT Ocean AeroCMIP)
    if ( ! -f ${localRoot}/db/${reg}Ave${component}.db ) then
      cp -fv ${refineDiagDir}/${oname}.${reg}Ave${component}.db ${localRoot}/db/${reg}Ave${component}.db
    else
      python vitals/python/merge.py ${refineDiagDir}/${oname}.${reg}Ave${component}.db ${localRoot}/db/${reg}Ave${component}.db
    endif
  end 
end

#-- Make an archive of the single-year sqlite files
set savepath = /archive/${USER}/`echo ${archive} | cut -f 4-100 -d '/'`
mkdir -p ${savepath}/ascii
pushd ${refineDiagDir}
foreach f (*.db)
  if ( ! -f ${savepath}/ascii/sqlite_files.tar ) then
    tar -cvf ${savepath}/ascii/sqlite_files.tar $f
  else
    tar -rvf ${savepath}/ascii/sqlite_files.tar $f
  endif
end
popd
