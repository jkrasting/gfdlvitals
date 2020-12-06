""" Utilities for merging DB files """

import sqlite3

__all__ = ["merge"]


def merge(source, destination):
    """Merges two sqlite files

    Parameters
    ----------
    source : str, path-like
        Path to source sqlite file
    destination : str, path-like
        Path to destination sqlite file
    """
    con = sqlite3.connect(destination)
    cur = con.cursor()
    sql = "ATTACH '" + source + "' as src"
    cur.execute(sql)
    cur.close()
    cur = con.cursor()
    sql = "SELECT * FROM main.sqlite_master WHERE type='table'"
    cur.execute(sql)
    cur.close()
    cur = con.cursor()
    sql = "SELECT * FROM src.sqlite_master WHERE type='table'"
    cur.execute(sql)
    src_tables = cur.fetchall()
    cur.close()
    for var in src_tables:
        varname = var[1]
        if varname not in [x[1] for x in src_tables]:
            cur = con.cursor()
            cur.execute(var[-1])
            cur.close()
        cur = con.cursor()
        sql = "INSERT OR REPLACE into " + varname + " SELECT * FROM src." + varname
        cur.execute(sql)
        cur.close()
    con.commit()
    con.close()
