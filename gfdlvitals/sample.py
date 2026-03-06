""" Sample db files for demonstration """

from importlib.resources import files

historical = str(files("gfdlvitals").joinpath("resources/historical.db"))
picontrol = str(files("gfdlvitals").joinpath("resources/picontrol.db"))
