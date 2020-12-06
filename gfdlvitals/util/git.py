""" Module for working with top-level git repository """

import os
import subprocess
import sys

__all__ = ["is_clean", "retrieve_commit"]


def is_clean(path):
    """Determines if a git repository is clean

    Parameters
    ----------
    path : str, path-like
        Path to git repository

    Returns
    -------
    bool
        True if clean, False if modified
    """
    retcode = _status(path)
    return retcode == 0


def retrieve_commit(path):
    """Returns current git commit

    Parameters
    ----------
    path : str, path-like
        Path to git repository

    Returns
    -------
    str
        Git commit hash
    """
    cwd = os.getcwd()
    os.chdir(path)
    cmd = "git rev-parse HEAD"
    commit = subprocess.check_output(cmd.split(" "))
    commit = str(commit.decode("utf-8")).replace("\n", "")
    os.chdir(cwd)
    return commit


def _status(path):
    """Internal subprocess call to query status of git repo

    Parameters
    ----------
    path : str, path-like
        Path to git repository

    Returns
    -------
    int
        Return code of system call to `git diff-index`
    """
    cwd = os.getcwd()
    os.chdir(path)
    cmd = "git diff-index --quiet HEAD"
    result = subprocess.run(cmd.split(" "), stdout=subprocess.DEVNULL, check=False)
    os.chdir(cwd)
    return result.returncode


if __name__ == "__main__":
    PATH = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
    COMMIT = retrieve_commit(PATH)
    print(COMMIT)
    RETCODE = _status(PATH)
    print(RETCODE)
    CLEAN = is_clean(PATH)
    print(CLEAN)
