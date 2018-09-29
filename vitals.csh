#------------------------------------------------------------------------------
#  vitals refineDiag.csh
#------------------------------------------------------------------------------

#-- Before anything, get the directory where this script lives
set sourced = `ls -l /proc/$$/fd | sed -e 's/^[^/]*//' | grep "/vitals.csh"`
set sourced = `dirname ${sourced}`
echo ${sourced}

echo "  ---------- begin vitals_refineDiag.csh --------  "
date

#-- Unload any previous versions of Python and load the system default
module unload python
module unload cdat
module load python

#-- Create a directory to house the sqlite database (if it does not already exist)
if (! -d ../db) then 
  mkdir -p ../db
endif

#-- Copy in the python tools to the working directory
unalias cp
cp -rfvp ${sourced}/python .

#-- Set oname variable and set up a directory for temporary output
set oname = `dir -1 *.nc | head -n 1 | cut -f 1 -d '.'`
set tempDir = `mktemp -d`
echo ${tempDir}

#-- Run the averager script
python vitals/python/global_average_cubesphere.py ${oname} ${refineDiagDir} Atmos atmos_month,atmos_co2_month
python vitals/python/global_average_cubesphere.py ${oname} ${refineDiagDir} AtmosAer atmos_month_aer
python vitals/python/global_average_land.py ${oname} ${refineDiagDir} Land land_month
python vitals/python/global_average_ice.py ${oname} ${refineDiagDir} Ice ice_month
python vitals/python/global_average_tripolar.py ${oname} ${refineDiagDir} COBALT ocean_cobalt_sfc,ocean_cobalt_misc,ocean_cobalt_tracers_year,ocean_cobalt_tracers_int
python vitals/python/extract_ocean_scalar.py ${oname} ${refineDiagDir}
python vitals/python/global_average_cubesphere.py ${oname} ${refineDiagDir} AeroCMIP aerosol_month_cmip

#-- Copy the database back to its original location
foreach reg (global nh sh tropics)
  foreach component (Atmos AtmosAer Land Ice COBALT Ocean AeroCMIP)
    if ( -f ${tempDir}/${oname}.${reg}Ave${component}.db ) then 
      if ( ! -f ../db/${reg}Ave${component}.db ) then
        cp -fv ${tempDir}/${oname}.${reg}Ave${component}.db ../db/${reg}Ave${component}.db
      else
        python python/merge.py ${tempDir}/${oname}.${reg}Ave${component}.db ../db/${reg}Ave${component}.db
      endif
    endif
  end 
end

#-- Clean up python directory
rm -fR python/

date
echo "  ---------- end vitals_refineDiag.csh ----------  "
