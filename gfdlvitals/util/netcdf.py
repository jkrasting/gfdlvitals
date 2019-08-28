import tarfile
import netCDF4

__all__ = ['extract_from_tar']

def extract_from_tar(tar,member):
    '''
    Function to extract a single netCDF file from within
    an uncompressed tarfile
    '''
    f = tar.extractfile(member)
    data = f.read()
    ds = netCDF4.Dataset("in-mem-file", mode='r', memory=data)
    return ds

