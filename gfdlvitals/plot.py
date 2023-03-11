""" Standardized plotting routines """

import warnings
import cftime
import nc_time_axis

import numpy as np
import pkg_resources as pkgr

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager

import gfdlvitals

__all__ = ["set_font", "plot_timeseries", "update_figure", "on_key", "run_plotdb"]

COUNT = 1


def set_font():
    """Sets font style to Roboto"""
    # Add Roboto font
    fonts_dir = pkgr.resource_filename("gfdlvitals", "resources/fonts")

    font_dirs = [fonts_dir]
    font_files = font_manager.findSystemFonts(fontpaths=font_dirs)

    for font_file in font_files:
        font_manager.fontManager.addfont(font_file)

    # Define fonts and sizes
    matplotlib.rcParams["font.family"] = "Roboto"
    matplotlib.rcParams.update({"font.size": 14})


def plot_timeseries(
    dsets,
    var,
    trend=False,
    align_times=False,
    plottype="average",
    smooth=None,
    nyears=None,
    labels=None,
    legend=True,
    means=True,
    title="both",
):
    """Standardized function to make a timeseries plot

    Parameters
    ----------
    dsets : gfdlvitals.VitalsDataFrame or list
        Dataframe or list of dataframes to plot
    var : str
        Variable name to plot
    trend : bool, optional
        Plot linear trend line if True, by default False
    align_times : bool, optional
        H, by default False
    plottype : str, optional
        Defines plot type as either "average" or "sum",
        by default "average"
    smooth : int, optional
        Integer number of years to apply smoothing, by default None
    nyears : int, optional
        Limit the x-axis to nyears number of points, by default None
    labels : str, optional
        Comma-separated list of dataset labels, by default None
    legend : bool, optional
        Display a legend for the plot, by default True
    means : bool, optional
        Add variable means to the legend, by default True
    title : str, optional
        Specify "varname", "longname", "both", or "none",
        by default "both"

    Returns
    -------
    matplotlib.pyplot.figure, dict
        Matplotlib figure handle and dictionary of axes/dataset mappings
    """

    set_font()

    # Ensure "dsets" is a list
    dsets = [dsets] if not isinstance(dsets, list) else dsets

    # Text Labels
    if labels is None:
        labels = [f"Dataset {x}" for x in range(0, len(dsets))]
        legend = False
    else:
        labels = labels.split(",")

    # Determine max length of time values
    maxlen = max([len(x.index) for x in dsets])

    # summed
    if plottype == "sum":
        dsets = [x.areasum() for x in dsets]

    # Compute trends if asked
    if trend:
        trends = [x.trend()[0:nyears] for x in dsets]

    if align_times:
        dsets = [x.extend(maxlen) for x in dsets]

    # Setup the figure. The top half will have a 16:9 aspect
    # ratio. The bottom half will be used for legend info and
    # the whole figure will be cropped at the end

    fig = plt.figure(figsize=(12, 6.75))
    ax1 = plt.subplot(1, 1, 1)

    # Establish a list of axes in the figure
    axes_dict = {}

    # If smoothing is requested, still plot a faint copy of the full timeseries
    for x, dset in enumerate(dsets):
        dset.attrs["alpha"] = 0.3 if smooth is not None else 1.0
        dset.attrs["color"] = f"C{x}"

    _lines = []

    for i, dset in enumerate(dsets):
        label = labels[i]

        axes_dict[label] = {}
        axes_dict[label]["data"] = dset

        # Determine if we need a twin time axis
        _ax = ax1.twiny() if align_times and i > 0 else ax1
        axes_dict[label]["axis"] = _ax

        axes_list = [axes_dict[x]["axis"] for x in list(axes_dict.keys())]

        # Keep a list of the axes and move new ones to the bottom of the figure
        if _ax not in list(axes_dict.keys()) and align_times:
            # Move twinned axis ticks and label from top to bottom
            _ax.xaxis.set_ticks_position("bottom")
            _ax.xaxis.set_label_position("bottom")

            # Offset the twin axis below the host
            _ax.spines["bottom"].set_position(("axes", -0.10 * (len(axes_dict) - 1)))

            # Make sure frame is displayed
            if i > 0:
                _ax.set_frame_on(True)
                # Turn on the frame for the twin axis, but then hide all
                # but the bottom spine
                _ax.patch.set_visible(False)
                _ = [sp.set_visible(False) for sp in _ax.spines.values()]
                _ax.spines["bottom"].set_visible(True)

        # Convert times to nc_time_axis
        times = [
            nc_time_axis.CalendarDateTime(item, "noleap") for item in dset.index.values
        ]

        # Add means to the labels
        _label = labels[i]
        if means:
            _mean = float(np.nanmean(dset[var].values[0:nyears]))
            _mean = round(_mean, 4)
            _label = f"{_label}  (mean={_mean})"
            labels[i] = _label

        # Make the first plot
        (axes_dict[label]["line"],) = _ax.plot(
            times[0:nyears],
            dset[var].values[0:nyears],
            color=dset.attrs["color"],
            alpha=dset.attrs["alpha"],
            label=_label,
        )

        _lines.append(axes_dict[label]["line"])

        # After the first plot is established, align time axes if asked
        if align_times:
            _time_index = dset.index[0:nyears]
            _ax.set_xlim(
                cftime.date2num(
                    _time_index[0], calendar="noleap", units="days since 2000-01-01"
                ),
                cftime.date2num(
                    _time_index[-1], calendar="noleap", units="days since 2000-01-01"
                ),
            )

        if trend:
            (axes_dict[label]["trendline"],) = _ax.plot(
                times[0 : len(trends[i])],
                trends[i][var].values[0:nyears],
                linestyle="dashed",
                color=dset.attrs["color"],
                alpha=1.0,
                linewidth=1,
            )
            axes_dict[label]["trend"] = trends[i]

        if smooth:
            (axes_dict[label]["smoothline"],) = _ax.plot(
                times[0:nyears],
                dset.smooth(smooth)[var].values[0:nyears],
                color=dset.attrs["color"],
                alpha=1.0,
                linewidth=2,
            )

        # Text annotations

        if i == 0:
            _varname = var if (title in ["varname", "both"]) else ""
            axes_dict[label]["topline_label"] = _ax.text(
                0.01, 1.08, _varname, ha="left", transform=ax1.transAxes, fontsize=22
            )

            _long_name = dset[var].attrs["long_name"]
            _long_name = f"Sum of {_long_name}" if plottype == "sum" else _long_name
            _long_name = _long_name if (title in ["longname", "both"]) else ""

            axes_dict[label]["longname_label"] = _ax.text(
                0.01,
                1.03,
                _long_name,
                ha="left",
                transform=ax1.transAxes,
                style="italic",
                fontsize=14,
                fontfamily="Roboto Condensed",
            )

            axes_dict[label]["units_label"] = _ax.set_ylabel(dset[var].attrs["units"])

    axes_list = [axes_dict[x]["axis"] for x in list(axes_dict.keys())]
    axes_list = list(set(axes_list))
    maxlim = max([x.get_xlim()[1] - x.get_xlim()[0] for x in axes_list])
    _ = [x.set_xlim(x.get_xlim()[0], x.get_xlim()[0] + maxlim) for x in axes_list]

    # Add grid
    _ = [x.grid(color="gray", linestyle="--", linewidth=0.3) for x in axes_list]

    if legend:
        plt.legend(
            _lines,
            labels,
            fancybox=True,
            framealpha=1,
            shadow=True,
            borderpad=0.5,
            loc="upper center",
            bbox_to_anchor=(0.5, (-0.10 * (len(axes_dict)) + 0.02)),
        )

    return fig, axes_dict


def update_figure(fig, axes_dict, varname, smooth, nyears, trend):
    """Update plot on keypress of left and right arrow keys

    Parameters
    ----------
    fig : matplotlib.pyplot.figure
        Matplotlib figure handle
    axes_dict : dict
        Internal structure of axes associations to the data
    varname : str
        Variable name to plot
    smooth : int, None type
        Integer number of years to apply as a smoother
    nyears : int, None type
        Integer number to years to limit the plotting
    trend : bool
        Add linear trend lines if True, omit if False

    Returns
    -------
    matplotlib.pyplot.figure
        Matplotlib figure handle
    """
    for i, label in enumerate(list(axes_dict.keys())):
        axes_dict[label]["line"].set_ydata(
            axes_dict[label]["data"][varname].values[0:nyears]
        )

        if trend:
            axes_dict[label]["trendline"].set_ydata(
                axes_dict[label]["trend"][varname].values[0:nyears]
            )

        if smooth:
            axes_dict[label]["smoothline"].set_ydata(
                axes_dict[label]["data"].smooth(smooth)[varname].values[0:nyears]
            )

        if i == 0:
            axes_dict[label]["topline_label"].set_text(varname)
            axes_dict[label]["longname_label"].set_text(
                axes_dict[label]["data"][varname].attrs["long_name"]
            )
            axes_dict[label]["units_label"].set_text(
                axes_dict[label]["data"][varname].attrs["units"]
            )

    axes_list = [axes_dict[x]["axis"] for x in list(axes_dict.keys())]
    _ = [ax.relim() for ax in axes_list]
    _ = [ax.autoscale(enable=True, axis="y") for ax in axes_list]

    fig.canvas.draw()

    return fig


def on_key(event, fig, varlist, axes_dict, smooth, nyears, trend):
    """Update plot on keypress of left and right arrow keys

    Parameters
    ----------
    event : mpl keyboard event
        Key press
    fig : matplotlib.pyplot.figure
        Matplotlib figure handle
    varlist : list
        List of variables to plot
    axes_dict : dict
        Internal structure of axes associations to the data
    smooth : int, None type
        Integer number of years to apply as a smoother
    nyears : int, None type
        Integer number to years to limit the plotting
    trend : bool
        Add linear trend lines if True, omit if False
    """
    global COUNT

    redraw = False

    if (event.key == "right") or (event.key == "left"):
        COUNT = (COUNT + 1) if event.key == "right" else (COUNT - 1)
        COUNT = 0 if COUNT < 0 else COUNT
        COUNT = len(varlist) - 1 if COUNT >= len(varlist) else COUNT
        varname = varlist[COUNT]
        redraw = True

    if redraw is True:
        _ = gfdlvitals.plot.update_figure(
            fig, axes_dict, varname, smooth, nyears, trend
        )


def run_plotdb(cliargs):
    """Intermediate function to execute plotting routines

    Parameters
    ----------
    cliargs : argparse.arguments
        Processed command-line arguments
    """
    dsets = [gfdlvitals.open_db(x) for x in cliargs.dbfiles]

    all_variables = [set(x.columns) for x in dsets]
    common_variables = set.intersection(*all_variables)

    extra_variables = [sorted(list(x - common_variables)) for x in all_variables]

    for x, _varlist in enumerate(extra_variables):
        if len(_varlist) > 0:
            print(
                "The following variables are availble only "
                + f"{cliargs.dbfiles[x]} and will not be plotted:\n"
            )

            if len(_varlist) % 2 != 0:
                _varlist.append(" ")

            split = int(len(_varlist) / 2)
            _list1 = _varlist[0:split]
            _list2 = _varlist[split:]
            for key, value in zip(_list1, _list2):
                print("{0:<20s} {1}".format(key, value))
            print("\n")

    variable_list = sorted(list(common_variables))

    mplfig, axes = gfdlvitals.plot.plot_timeseries(
        dsets,
        variable_list[0],
        trend=cliargs.trend,
        align_times=cliargs.align,
        smooth=cliargs.smooth,
        nyears=cliargs.nyears,
        labels=cliargs.labels,
    )
    _ = mplfig.canvas.mpl_connect(
        "key_press_event",
        lambda event: on_key(
            event,
            mplfig,
            variable_list,
            axes,
            cliargs.smooth,
            cliargs.nyears,
            cliargs.trend,
        ),
    )

    plt.tight_layout()
    plt.show(block=True)
