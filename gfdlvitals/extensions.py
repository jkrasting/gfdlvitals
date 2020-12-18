""" Pandas class extension for gfdlvitals """

import math
import sqlite3

import cftime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__all__ = ["VitalsDataFrame", "Timeseries", "open_db", "reformat_time_axis"]


def _remove_trend(x, y, order=1, anomaly=True, return_coefs=False, coefs=None):
    """Internal function to remove a linear trend

    Parameters
    ----------
    x : numpy.ndarray
        independent axis
    y : np.ndarray
        dependent axis
    order : int, optional
        Polynomial order to use for fitting, by default 1
    anomaly : bool, optional
        Results as anomalies from the fit, by default True
    return_coefs : bool, optional
        Return polynomial fit coeffiecients, by default False
    coefs : tuple, optional
        Use a provided set of coefficients, by default None

    Returns
    -------
    numpy.ndarray
        Detrended data
    """

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
    """Internal function to calculate trend line/curves

    Parameters
    ----------
    x : numpy.ndarray
        independent axis
    y : np.ndarray
        dependent axis
    order : int, optional
        Polynomial order to use for fitting, by default 1

    Returns
    -------
    numpy.ndarray
        Polynomial fit
    """

    idx = np.isfinite(x) & np.isfinite(y)
    coefs = np.polyfit(x[idx], y[idx], order)
    model = np.poly1d(coefs)
    return model(x)


def _remove_reference_trend(t, x, other, anomaly=True):
    """Removes trends from a reference dataset

    Parameters
    ----------
    t : numpy.ndarray
        independent axis
    x : gfdlvitals.VitalsDataFrame
        Dataset to be detrended
    other : gfdlvitals.VitalsDataFrame
        Reference dataset containing the trend to be removed
    anomaly : bool, optional
        Results as anomalies from the fit, by default True

    Returns
    -------
    gfdlvitals.VitalsDataFrame
        Detrended dataset
    """

    if str(x.name) not in list(other.columns):
        result = None
    else:
        _coefs = other[x.name].to_numpy()
        result = _remove_trend(t, x, anomaly=anomaly, coefs=_coefs)
    return result


def reformat_time_axis(ax=None):
    """Reformats x-axis labels to YYYY format

    Parameters
    ----------
    ax : matplotlob.pyplot.figure.axis, optional
        axis object to be reformatted, by default None
    """

    if ax is None:
        ax = plt.gca()
    labels = [x.get_text() for x in ax.xaxis.get_ticklabels()]
    labels = [x.split("-")[0] for x in labels]
    _ = ax.set_xticklabels(labels)


class VitalsDataFrame(pd.DataFrame):
    """Pandas class extension for holding the Vitals data

    Parameters
    ----------
    pd : pandas.DataFrame
        Input Pandas DataFrame object

    Returns
    -------
    gfdlvitals.VitalsDataFrame
        Class extension object
    """

    # temporary properties
    _internal_names = pd.DataFrame._internal_names + ["internal_cache"]
    _internal_names_set = set(_internal_names)

    # normal properties
    _metadata = ["added_property"]

    @property
    def _constructor(self):
        return VitalsDataFrame

    def smooth(self, window, extrap=False):
        """Apply a smoother to the dataset

        Parameters
        ----------
        window : int
            Smoothing filter length
        extrap : bool, optional
            Extrapolate data on the ends, by default False

        Returns
        -------
        self
            Smoothed dataset
        """

        if window is None:
            _df = self
        else:
            _df = self.rolling(window, center=True).mean()
            if extrap is True:
                _df.fillna(method="ffill", inplace=True)
                _df.fillna(method="bfill", inplace=True)
        _df.attrs = self.attrs
        return _df

    def extend(self, maxlen):
        """Extend VitalsDataFrame to a set length and pad with NaNs

        Parameters
        ----------
        maxlen : int
            New length of the VitalsDataFrame

        Returns
        -------
        self
            Extended dataset
        """
        endyear = tuple(self.index[-1].timetuple())
        padding = np.arange(1, maxlen - len(self.index) + 1) + endyear[0]
        added_index = [cftime.DatetimeNoLeap(x, *endyear[1:]) for x in padding]
        _df = pd.DataFrame({"times": added_index}).set_index("times")
        _df = self.append(_df)
        _df.attrs = self.attrs
        for column in self.columns:
            _df[column].attrs = self[column].attrs
        return _df

    def detrend(self, reference=None, order=1, anomaly=True, return_coefs=False):
        """Detrend VitalsDataFrame object

        Parameters
        ----------
        reference : gfdlvitals.DataFrame, optional
            Reference VitalsDataFrame, by default None
        order : int, optional
            Polynomial order to use for fitting, by default 1
        anomaly : bool, optional
            Results as anomalies from the fit, by default True
        return_coefs : bool, optional
            Return polynomial fit coeffiecients, by default False

        Returns
        -------
        self
            Extended dataset
        """
        tindex = np.array(
            [
                cftime.date2num(x, "days since 0001-01-01", calendar="noleap")
                for x in self.index
            ]
        )
        if reference is not None:
            if order != 1:
                print(
                    "Only a linear trend can be removed based on "
                    + "another dataset. Setting order to 1."
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
        result.attrs = self.attrs
        return result

    def trend(self, order=1):
        """Fits a trend to the VitalsDataFrame object

        Parameters
        ----------
        order : int, optional
            Polynomial order to use for fitting, by default 1

        Returns
        -------
        self
            Fitted trend dataset
        """
        tindex = np.array(
            [
                cftime.date2num(x, "days since 0001-01-01", calendar="noleap")
                for x in self.index
            ]
        )
        result = self.apply(lambda x: (_calc_trend(tindex, x, order=order)))
        result.attrs = self.attrs
        return result


class Timeseries:
    """Timeseries class object

    Parameters
    ----------
    f : str, path-like
        Input SQLite file
    var : str
        Variable to extract
    scale : float, optional
        Scale data by this factor, by default 1.0
    multiply_by_area : bool, optional
        Multiply variable by cell area before returning, by default False
    legacy_land : bool, optional
        Read legacy version of the land SQLite files, by default False
    start : int, optional
        Specify start year, by default None
    end : int, optional
        Specify end year, by default None
    """

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
        _ = cur.execute("SELECT name FROM sqlite_master where TYPE='table'")
        tables = [str(record[0]) for record in cur.fetchall()]
        if multiply_by_area is True:
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
        if "long_name" in tables:
            _ = cur.execute(f"SELECT value FROM long_name where var='{var}'")
            result = cur.fetchone()
            self.long_name = result[0] if isinstance(result,tuple) else None
        else:
            self.long_name = None
        if "units" in tables:
            _ = cur.execute(f"SELECT value FROM units where var='{var}'")
            result = cur.fetchone()
            self.units = result[0] if isinstance(result,tuple) else None
        else:
            self.units = None
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
    attributes = {}
    years = []
    skipped = []
    for var in variables:
        tsobj = Timeseries(
            dbfile, var, legacy_land=legacy_land, start=start, end=end
        )
        if len(tsobj.t) > 0:
            data[var] = tsobj.data
            years = years + list(tsobj.t)
            attributes[var] = {"long_name": tsobj.long_name, "units": tsobj.units}

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

    for var in list(df.columns):
        df[var].attrs = attributes[var]

    return df
