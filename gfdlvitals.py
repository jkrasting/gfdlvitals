#!/home/mdteam/miniconda3-pub/envs/det_py3_201906/bin/python

import argparse
import gfdlvitals
import glob
import os
import shutil
import subprocess
import tempfile

__version__ = "2.0.0"


def arguments():
    '''
    Function to capture the user-specified command line options
    '''
    description = '''
    Program for generating global mean statistics directly 
    from history tarfile.

    For help, contact John.Krasting@noaa.gov

    '''

    parser = argparse.ArgumentParser(description=description, 
                 formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('historydir', metavar='HISTORY DIR', type=str,
        default=os.getcwd(), help='Path to /history directory')

    parser.add_argument('-o', '--outdir', type=str, default='./',
        help='Output directory. Default is current directory')

    parser.add_argument('-m', '--modelclass', type=str, default='CM4',
        help='Model class. Options include CM4 and ESM2. Default is CM4')

    parser.add_argument('-s', '--startyear', type=int, default=None,
        help='Starting year to process. Default is all years.')

    parser.add_argument('-e', '--endyear', type=int, default=None,
        help='Ending year to process. Default is all years.')

    parser.add_argument('-g', '--gridspec', type=str, default=None,
        help='Path to gridspec tarfile. Used in AMOC calculation. '+
             'Default is None')

    return parser.parse_args()



def process_year(args,infile):
    #-- Set the model year string
    fYear = str(infile.split('/')[-1].split('.')[0])
    if args.modelclass == 'ESM2':
        gfdlvitals.models.ESM2.routines(args,infile)
    if args.modelclass == 'ESM4':
        gfdlvitals.models.ESM4.routines(args,infile)
    #-- Move results to their final location 
    if not os.path.exists(args.outdir):
      os.makedirs(args.outdir)
    for reg in ['global','nh','sh','tropics']:
      for component in ['Land','Atmos','Ocean','Ice','TOPAZ']:
        if os.path.exists(fYear+'.'+reg+'Ave'+component+'.db'):
          if not os.path.exists(args.outdir+'/'+reg+'Ave'+component+'.db'):
            shutil.copyfile(fYear+'.'+reg+'Ave'+component+'.db',args.outdir+\
                '/'+reg+'Ave'+component+'.db')
          else:
            gfdlvitals.util.merge.merge(fYear+'.'+reg+'Ave'+component+'.db',
                args.outdir+'/'+reg+'Ave'+component+'.db')



if __name__ == '__main__':
    args = arguments()

    #-- Obtain git commit hash for provenance
    script_dir = os.path.dirname(os.path.abspath(__file__))
    args.commit = gfdlvitals.util.git.retrieve_commit(script_dir)
    print('Using gfdlvitals version '+__version__+' -- git version '
        +args.commit)

    #-- Get a list of history files
    dirlist = sorted(glob.glob(args.historydir+"/*.tar"))

    #-- Apply start and end year limits, if applicable
    infiles = []
    if (args.startyear is not None) or (args.endyear is not None):
        if args.startyear is None:
            args.startyear = -1
        if args.endyear is None:
            args.endyear = 99999
        for f in dirlist:
            yr = int(os.path.basename(f)[0:4])
            if (yr >= args.startyear) and (yr <= args.endyear):
                infiles.append(f)
    else:
        infiles = dirlist

    #-- DMGET the history files
    print('Dmgetting files ...')
    subprocess.call(['dmget']+infiles)
    print('Complete!')

    #-- Make temporary directory to work in 
    cwd = os.getcwd()
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)

    #-- Loop over history files
    for infile in infiles:
        process_year(args,infile)
    
    #-- Clean up 
    os.chdir(cwd)
    shutil.rmtree(tempdir)

    exit()
