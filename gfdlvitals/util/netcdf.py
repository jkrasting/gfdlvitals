import tarfile
import netCDF4

__all__ = ['extract_from_tar','in_mem_nc']

def extract_from_tar(tar,member,ncfile=False):
    '''
    Function to extract a single netCDF file from within
    an uncompressed tarfile
    '''
    f = tar.extractfile(member)
    data = f.read()
    if ncfile:
        data = in_mem_nc(data)
    return data


def in_mem_nc(data):
    return netCDF4.Dataset("in-mem-file", mode='r', memory=data)
