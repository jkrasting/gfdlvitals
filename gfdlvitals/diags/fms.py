from gfdlvitals.util import gmeantools
import tarfile as tf
import pandas as pd
import io

__all__ = ['timing']

def timing(f,fYear,outdir,label):

    def ascii_tar_to_stats_df(f):
        """Subroutine to read fms.out from ascii tar file, extract the clock
           timings, and return a pandas dataframe"""
    
        tar = tf.open(f)
        for member in tar.getnames():
            if "fms.out" in member:
                break
    
        f=tar.extractfile(member)
        content=f.readlines()
        for n,l in enumerate(content):
            if "Total runtime" in l.decode('utf-8'):
                break
        tar.close()
        content = content[n::]
    
        output = io.BytesIO()
        output.write(str.encode("clock,min,max,mean,std\n"))
        for l in content:
            l = l.decode('utf-8')
            if l.startswith(' '):
                continue
            else:
                l = l.split()
                l = l[-1::-1]
                label = ' '.join(l[8::][-1::-1])
                label = label.replace(' ','_')
                label = label.replace('-','_')
                label = label.replace('&','_')
                for x in ['(',')','*','/',':']:
                    label = label.replace(x,'')
                l = [label] + l[0:8][-1::-1][0:4]
                l = ','.join(l) + '\n'
                output.write(str.encode(l))
        output.seek(0)
    
        df = pd.read_csv(output,delimiter=',')
        # df = df.set_index('clock')
    
        return df
    
    df = ascii_tar_to_stats_df(f)

    clocks = sorted(df['clock'].to_list())
    for clock in clocks:
        for attr in ['mean','min','max']:
            val = df[df['clock'] == clock][attr].values[0]

            #-- Write to sqlite
            gmeantools.write_sqlite_data(outdir+'/'+fYear+'.globalAve'+label+'.db',
            clock+'_'+attr,fYear[:4],val)
