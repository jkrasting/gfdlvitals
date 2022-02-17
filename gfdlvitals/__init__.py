"""gfdlvitals - a package for computing global mean metrics"""

from .version import __version__

from . import averagers
from . import cli
from . import models
from . import sample
from . import util
from .extensions import *
from .plot import *

__all__ = [
    "averagers",
    "cli",
    "models",
    "util",
    "VitalsDataFrame",
    "open_db",
    "plot_timeseries",
]
