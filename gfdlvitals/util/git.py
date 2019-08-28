import os
import subprocess
import sys

__ALL__ = ['retrieve_commit','status']

def is_clean(path):
    rc = status(path)
    if rc == 0:
      clean = True
    else:
      clean = False
    return clean

def retrieve_commit(path):
    cwd = os.getcwd()
    os.chdir(path)
    cmd = 'git rev-parse HEAD'
    commit = subprocess.check_output(cmd.split(' '))
    commit = str(commit.decode('utf-8')).replace('\n','')
    os.chdir(cwd)
    return commit

def status(path):
    cwd = os.getcwd()
    os.chdir(path)
    cmd = 'git diff-index --quiet HEAD'
    result = subprocess.run(cmd.split(' '), stdout=subprocess.DEVNULL)
    os.chdir(cwd)
    return result.returncode



if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = os.path.abspath(sys.argv[1])
    else:
        path = os.getcwd()
    commit = retrieve_commit(path)
    print(commit)
    rc = status(path)
    print(rc)
    clean = is_clean(path)
    print(clean)
