""" Pandas class extension for gfdlvitals """

import copy
import datetime
import math
import sqlite3
import warnings

import cftime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy import stats

__all__ = [
    "VitalsDataFrame",
    "Timeseries",
    "open_db",
    "reformat_time_axis",
    "ttest_ind_auto",
]


def _autocorr(arr, lag=1):
    """Computes the sample autocorrelation function coeffficient (rho)
    for given lag

    Parameters
    ----------
    arr : numpy.array (1-d)
        Input data array
    lag : int, optional
        lag, by default 1

    Returns
    -------
    float
        lagged auto-correlation
    """

    flen = float(len(arr))
    ybar = float(sum(arr)) / flen
    denom = sum([(y - ybar) ** 2 for y in arr])
    numer = sum(
        [(y - ybar) * (ytpk - ybar) for (y, ytpk) in zip(arr[:-lag], arr[lag:])]
    )
    return numer / denom


def ttest_ind_auto(arr1, arr2, axis=0):
    """Performs a t-test that adjusts the degrees of freedom
    based on the autocorrelation of the dataset.
    See Krasting et al. 2013 for more details
    DOI: 10.1175/JCLI-D-12-00832.1

    Parameters
    ----------
    arr1 : numpy.ndarray
        First array of data points
    arr2 : numpy.ndarray
        Second array of data points
    axis : int, optional
        Axis to perform t-test, by default 0

    Returns
    -------
    tuple
        t-statistic, probability,
        arr1 autocorrelation, arr2 autocorrelation
    """
    arr1, arr2, axis = _chk2_asarray(arr1, arr2, axis)
    variance1 = np.var(arr1, axis, ddof=1)
    variance2 = np.var(arr2, axis, ddof=1)
    arrlen1 = arr1.shape[axis]
    arrlen2 = arr2.shape[axis]
    lag1r1 = _autocorr(np.split(arr1, arr1.shape[axis], axis))
    lag1r2 = _autocorr(np.split(arr2, arr2.shape[axis], axis))
    n1eff = arrlen1 * ((1 - lag1r1) / (1 + lag1r1))
    n2eff = arrlen2 * ((1 - lag1r2) / (1 + lag1r2))
    df = n1eff + n2eff - 2
    diff = np.mean(arr1, axis) - np.mean(arr2, axis)
    svar = ((arrlen1 - 1) * variance1 + (arrlen2 - 1) * variance2) / float(df)
    t = diff / np.sqrt(svar * (1.0 / arrlen1 + 1.0 / arrlen2))
    t = np.where((diff == 0) * (svar == 0), 1.0, t)  # define t=0/0 = 0, identical means
    prob = stats.distributions.t.sf(np.abs(t), df) * 2
    # use np.abs to get upper tail
    # distributions.t.sf currently does not propagate nans
    # this can be dropped, if distributions.t.sf propagates nans
    # if this is removed, then prob = prob[()] needs to be removed
    prob = np.where(np.isnan(t), np.nan, prob)
    if t.ndim == 0:
        t = t[()]
        prob = prob[()]
    result = [t, prob, lag1r1, lag1r2]
    result = [float(x) for x in result]
    return tuple(result)


def _chk2_asarray(arr1, arr2, axis):
    if axis is None:
        arr1 = np.ravel(arr1)
        arr2 = np.ravel(arr2)
        outaxis = 0
    else:
        arr1 = np.asarray(arr1)
        arr2 = np.asarray(arr2)
        outaxis = axis
    return arr1, arr2, outaxis


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

    def build_netrad_toa(self):
        """Constructs netrad_toa from component terms if available

        Parameters
        ----------
        self : VitalsDataFrame

        Returns
        -------
        VitalsDataFrame
        """

        varlist = list(self.columns)
        if ("netrad_toa" not in varlist) and (
            all(x in varlist for x in ["swdn_toa", "swup_toa", "olr"])
        ):
            self["netrad_toa"] = self["swdn_toa"] - self["swup_toa"] - self["olr"]

            self["netrad_toa"].attrs = {
                "long_name": "Net TOA Radiation "
                + "(resconstructed as swdn_toa - swup_toa - olr)",
                "units": "W m-2",
            }

        return self

    def areasum(self):
        """Returns the area integrated variable based
        on the cell_measure method
        """
        cell_measures = [(x, self[x].attrs["cell_measure"]) for x in list(self.columns)]
        varlist, cm_set = zip(*cell_measures)
        cm_set = [x for x in list(set(cm_set)) if x is not None]
        attrs = {x: self[x].attrs for x in varlist}
        cell_measures = [x for x in cell_measures if x[0] not in cm_set]

        result = {}

        for x in cell_measures:
            if x[1] is not None:
                try:
                    _res = self[x[0]] * self[x[1]]
                    _res.attrs = attrs[x[0]]
                    result[x[0]] = _res

                except Exception as exc:
                    warnings.warn(f"Unable to sum field {x[0]}")

        result = pd.DataFrame(result)
        result = VitalsDataFrame(result)

        for var in list(result.columns):
            result[var].attrs = attrs[var]

        return result

    def ttest(self, df2):
        """Performs t-test between two instances of VitalsDataFrame

        Parameters
        ----------
        df2 : VitalsDataFrame
            Comparison data set

        Returns
        -------
        pandas.DataFrame
            Contains p-values for variables common between the
            two VitalsDataFrames
        """

        # get a list of common variables
        varlist = list(set(self.columns).intersection(df2.columns))

        # ignore some known fields
        ignore_list = ["area"]
        varlist = [x for x in varlist if x not in ignore_list]

        # perform t-test
        result = {k: ttest_ind_auto(self[k], df2[k])[1] for k in varlist}

        return pd.DataFrame(result, index=["pval"]).transpose()

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
        _df = pd.concat([self,_df])
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

        # convert ISO index to datetime object
        if isinstance(self.index[0], str):
            self.index = [datetime.datetime.fromisoformat(x) for x in self.index]

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

        # open the sqlite connection
        con = sqlite3.connect(f)
        cur = con.cursor()

        # get the results from the sqlite file for the requested variable
        if legacy_land is True:
            _ = cur.execute(f"SELECT year,sum FROM {var} ORDER BY year ASC")
        else:
            _ = cur.execute(f"SELECT year,value FROM {var} ORDER BY year ASC")
        results = cur.fetchall()

        # split list of tuples into two different lists
        self._t, self._data = zip(*results)
        self._t = np.array(self._t)

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

        self._data = np.array(self._data) * scale

        if "long_name" in tables:
            _ = cur.execute(f"SELECT value FROM long_name where var='{var}'")
            result = cur.fetchone()
            self.long_name = result[0] if isinstance(result, tuple) else None
        else:
            self.long_name = None

        if "units" in tables:
            _ = cur.execute(f"SELECT value FROM units where var='{var}'")
            result = cur.fetchone()
            self.units = result[0] if isinstance(result, tuple) else None
        else:
            self.units = None

        if "cell_measure" in tables:
            _ = cur.execute(f"SELECT value FROM cell_measure where var='{var}'")
            result = cur.fetchone()
            self.cell_measure = result[0] if isinstance(result, tuple) else None
        else:
            self.cell_measure = None

        # close the connection
        cur.close()
        con.close()

        # filter based on start year and end year
        if start is not None:
            idx = [i for i, val in enumerate(self._t) if val >= start]
            self._t = self._t[idx]
            self._data = self._data[idx]
        else:
            start = self._t.min()
        if end is not None:
            idx = [i for i, val in enumerate(self._t) if val <= end]
            self._t = self._t[idx]
            self._data = self._data[idx]
        else:
            end = self._t.max() + 1

        # check for missing values and pad with nans
        missing_times = set(np.arange(start, end)) - set(self._t)
        if len(list(missing_times)) != 0:
            warnings.warn(f"Timeseries is incomplete for {var}: {missing_times}")

        # pad missing values with nans
        self.dict = dict(zip(self._t, self._data))
        self.dict = {
            **self.dict,
            **dict(zip(missing_times, [np.nan] * len(missing_times))),
        }

    @property
    def t(self):
        k, v = zip(*sorted(self.dict.items()))
        return k

    @property
    def data(self):
        k, v = zip(*sorted(self.dict.items()))
        return v

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
        tsobj = Timeseries(dbfile, var, legacy_land=legacy_land, start=start, end=end)
        if len(tsobj.t) > 0:
            data[var] = tsobj.data
            years = years + list(tsobj.t)
            attributes[var] = {
                "long_name": tsobj.long_name,
                "units": tsobj.units,
                "cell_measure": tsobj.cell_measure,
            }

    years = sorted(list(set(years)))
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
    df = df.sort_index()

    for var in list(df.columns):
        df[var].attrs = attributes[var]

    return df
