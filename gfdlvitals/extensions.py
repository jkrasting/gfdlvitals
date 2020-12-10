""" Pandas class extension for gfdlvitals """

import math
import sqlite3

import cftime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__all__ = ["VitalsDataFrame", "Timeseries", "open_db"]


def _remove_trend(x, y, order=1, anomaly=True, return_coefs=False, coefs=None):
    """Internal function to remove a linear trend"""
    if None in list(y):
        return None
    if coefs is None:
        idx = np.isfinite(x) & np.isfinite(y)
        coefs = np.polyfit(x[idx], y[idx], order)
        if return_coefs is True:
            return coefs
    model = np.poly1d(coefs)
    fit = model(x)
    if anomaly is True:
        result = y - fit
    else:
        fit = fit - fit[0]
        result = y - fit
    return result


def _calc_trend(x, y, order=1):
    """Internal function to calculate trend line/curve"""
    idx = np.isfinite(x) & np.isfinite(y)
    coefs = np.polyfit(x[idx], y[idx], order)
    model = np.poly1d(coefs)
    return model(x)


def _remove_reference_trend(t, x, other, anomaly=True):
    """Removes trends from a reference dataset"""
    if str(x.name) not in list(other.columns):
        result = None
    else:
        _coefs = other[x.name].to_numpy()
        result = _remove_trend(t, x, anomaly=anomaly, coefs=_coefs)
    return result

def reformat_time_axis(ax=None):
    """Reformats x-axis labels to YYYY format"""
    if ax is None:
        ax = plt.gca()
    labels = [x.get_text() for x in ax.xaxis.get_ticklabels()]
    labels = [x.split("-")[0] for x in labels]
    _ = ax.set_xticklabels(labels)


class VitalsDataFrame(pd.DataFrame):
    # temporary properties
    _internal_names = pd.DataFrame._internal_names + ["internal_cache"]
    _internal_names_set = set(_internal_names)

    # normal properties
    _metadata = ["added_property"]

    @property
    def _constructor(self):
        return VitalsDataFrame

    def smooth(self, window, extrap=False):
        _df = self.rolling(window, center=True).mean()
        if extrap is True:
            _df.fillna(method="ffill", inplace=True)
            _df.fillna(method="bfill", inplace=True)
        return _df

    def detrend(self, reference=None, order=1, anomaly=True, return_coefs=False):
        tindex = np.array(
            [
                cftime.date2num(x, "days since 0001-01-01", calendar="noleap")
                for x in self.index
            ]
        )
        if reference is not None:
            if order != 1:
                print(
                    "Only a linear trend can be removed based on "+
                    "another dataset. Setting order to 1."
                )
                order = 1
            coefs = reference.detrend(order=order, return_coefs=True)
            result = self.apply(
                lambda x: (_remove_reference_trend(tindex, x, coefs, anomaly=anomaly))
            )
        else:
            result = self.apply(
                lambda x: (
                    _remove_trend(
                        tindex,
                        x,
                        order=order,
                        anomaly=anomaly,
                        return_coefs=return_coefs,
                    )
                )
            )
        return result

    def trend(self, order=1):
        tindex = np.array(
            [
                cftime.date2num(x, "days since 0001-01-01", calendar="noleap")
                for x in self.index
            ]
        )
        return self.apply(lambda x: (_calc_trend(tindex, x, order=order)))


class Timeseries:
    def __init__(
        self,
        f,
        var,
        scale=1.0,
        multiply_by_area=False,
        legacy_land=False,
        start=None,
        end=None,
    ):
        con = sqlite3.connect(f)
        cur = con.cursor()
        if legacy_land is True:
            _ = cur.execute("SELECT year,sum FROM " + var)
        else:
            _ = cur.execute("SELECT year,value FROM " + var)
        results = cur.fetchall()
        self.t, self.data = zip(*results)
        self.t = np.array(self.t)
        if multiply_by_area is True:
            _ = cur.execute("SELECT name FROM sqlite_master where TYPE='table'")
            tables = [str(record[0]) for record in cur.fetchall()]
            if "cell_measure" in tables:
                _ = cur.execute(
                    "SELECT value FROM cell_measure where var='" + var + "'"
                )
                cell_measure = cur.fetchone()[0]
            else:
                cell_measure = "area"
            _ = cur.execute("SELECT value FROM " + cell_measure)
            area = np.array(cur.fetchall()).squeeze()
            scale = area * scale
        self.data = np.array(self.data) * scale
        cur.close()
        con.close()
        if start is not None:
            idx = [i for i, val in enumerate(self.t) if val >= start]
            self.t = self.t[idx]
            self.data = self.data[idx]
        else:
            start = self.t.min()
        if end is not None:
            idx = [i for i, val in enumerate(self.t) if val <= end]
            self.t = self.t[idx]
            self.data = self.data[idx]
        else:
            end = self.t.max() + 1
        missing_times = set(np.arange(start, end)) - set(self.t)
        if len(list(missing_times)) != 0:
            print("# WARNING: Timeseries is incomplete for " + var, missing_times)
        self.dict = dict(zip(self.t, self.data))

    def __str__(self):
        return self.__class__.__name__

    def __hash__(self):
        return hash([self.__dict__[x] for x in list(self.__dict__.keys())])

def open_db(
    dbfile,
    variables=None,
    yearshift=0.0,
    legacy_land=False,
    start=None,
    end=None,
):
    """Function to read sqlite dbfile"""

    if variables is None:
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        _ = cur.execute(sql)
        variables = [str(record[0]) for record in cur.fetchall()]
        cur.close()
        conn.close()
        removes = ["units", "long_name", "cell_measure"]
        variables = [x for x in variables if x not in removes]

    # -- Loop over variables
    data = {}
    years = []
    skipped = []
    for var in variables:
        try:
            tsobj = Timeseries(dbfile, var, legacy_land=legacy_land, start=start, end=end)
            if len(tsobj.t) > 0:
                data[var] = tsobj.data
                years = years + list(tsobj.t)
        except:
            skipped.append(var)

    years = list(set(years))
    years = [x + float(yearshift) for x in years]

    variables = list(set(variables) - set(skipped))

    if start is None:
        start = -1 * math.inf

    if end is None:
        end = math.inf

    df = pd.DataFrame(data, index=years)
    df = df[(df.index >= start) & (df.index <= end)]
    df.index = cftime.num2date(
        (df.index * 365.0) - (365.0 / 2.0) - 1,
        "days since 0001-01-01",
        calendar="365_day",
    )
    df = VitalsDataFrame(df)
    return df
