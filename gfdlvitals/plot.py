import imp

import cftime
import nc_time_axis

import gfdlvitals
import matplotlib
import matplotlib.pyplot as plt

import os
from matplotlib import font_manager as fm, rcParams
import matplotlib.pyplot as plt
from matplotlib import font_manager

__all__ = ["plot_variable"]


def plot_variable(dsets, var, nyears=None, smooth=None, trend=False, align_times=False):

    # Ensure "dsets" is a list
    dsets = [dsets] if not isinstance(dsets, list) else dsets

    # Determine max length of time values
    maxlen = max([len(x.index) for x in dsets])

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
    axes_list = [ax1]

    # If smoothing is requested, still plot a faint copy of the full timeseries
    for x, dset in enumerate(dsets):
        dset.attrs["alpha"] = 0.3 if smooth is not None else 1.0
        dset.attrs["color"] = f"C{x}"

    for n, dset in enumerate(dsets):

        # Convert times to nc_time_axis
        times = [
            nc_time_axis.CalendarDateTime(item, "noleap") for item in dset.index.values
        ]
        _times = [
            nc_time_axis.CalendarDateTime(item, "noleap")
            for item in dsets[0].index.values
        ]

        # Determine if we need a twin time axis
        _ax = ax1.twiny() if align_times and n > 0 else ax1

        # Keep a list of the axes and move new ones to the bottom of the figure
        if _ax not in axes_list:
            axes_list.append(_ax)
            # Move twinned axis ticks and label from top to bottom
            _ax.xaxis.set_ticks_position("bottom")
            _ax.xaxis.set_label_position("bottom")

            # Offset the twin axis below the host
            _ax.spines["bottom"].set_position(("axes", -0.10 * (len(axes_list) - 1)))

            # Turn on the frame for the twin axis, but then hide all
            # but the bottom spine
            _ax.set_frame_on(True)
            _ax.patch.set_visible(False)
            _ = [sp.set_visible(False) for sp in _ax.spines.values()]
            _ax.spines["bottom"].set_visible(True)

        # Make the first plot
        _ax.plot(
            times[0:nyears],
            dset[var].values[0:nyears],
            color=dset.attrs["color"],
            alpha=dset.attrs["alpha"],
        )

        # Make the smoothed plot
        if smooth is not None:
            _ax.plot(
                times[0:nyears],
                dset.smooth(smooth)[var].values[0:nyears],
                color=dset.attrs["color"],
                alpha=1.0,
                linewidth=2,
            )

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
            _ax.plot(
                times[0 : len(trends[n])],
                trends[n][var].values[0 : len(trends[n])],
                linestyle="dashed",
                color=dset.attrs["color"],
                alpha=1.0,
                linewidth=1,
            )

        # If this is the first dataset, add labels to the plot
        ax1.text(
            0.01,
            1.03,
            dset[var].attrs["long_name"],
            ha="left",
            transform=ax1.transAxes,
            style="italic",
            fontsize=14,
            fontfamily="Roboto Condensed",
        )
        ax1.text(0.01, 1.08, var, ha="left", transform=ax1.transAxes, fontsize=22)
        ax1.set_ylabel(dset[var].attrs["units"])
        ax1.set_xlabel("Model Year")

    maxlim = max([x.get_xlim()[1] - x.get_xlim()[0] for x in axes_list])
    _ = [x.set_xlim(x.get_xlim()[0], x.get_xlim()[0] + maxlim) for x in axes_list]

    # Add grid
    _ = [x.grid(color="gray", linestyle="--", linewidth=0.3) for x in axes_list]

    plt.tight_layout()

    return fig
