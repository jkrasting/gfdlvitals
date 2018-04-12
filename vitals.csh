#------------------------------------------------------------------------------
#  vitals refineDiag.csh
#------------------------------------------------------------------------------

#-- Before anything, get the directory where this script lives
set sourced=($_)
if ("${sourced}" != "") then
    set sourced = `echo ${sourced} | cut -f 2 -d ' '`
    set sourced = `dirname ${sourced}`
    echo "${sourced}"
endif

set sourced = "/nbhome/jpk/projects/vitals"

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
python python/global_average_cubesphere.py ${oname} ${tempDir} Atmos atmos_month,atmos_co2_month
python python/global_average_cubesphere.py ${oname} ${tempDir} AtmosAer atmos_month_aer
python python/global_average_land.py ${oname} ${tempDir} Land land_month
python python/global_average_ice.py ${oname} ${tempDir} Ice ice_month
python python/global_average_tripolar.py ${oname} ${tempDir} COBALT ocean_cobalt_sfc,ocean_cobalt_misc,ocean_cobalt_tracers_year,ocean_cobalt_tracers_int
python python/extract_ocean_scalar.py ${oname} ${tempDir}

#-- Copy the database back to its original location
foreach reg (global nh sh tropics)
  foreach component (Atmos AtmosAer Land Ice COBALT Ocean)
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
