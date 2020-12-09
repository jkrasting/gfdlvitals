""" Utiliites for use in averaging routines """

__all__ = ["RichVariable"]


class RichVariable:
    """Metadata-rich variable class

    Parameters
    ----------
    varname : str
        Variable name
    grid_file : io.BufferedReader or list of io.BufferedReader
        Grid-spec tiles
    data_file : io.BufferedReader or list of io.BufferedReader
        Data tiles
    fyear : str
        Year that is being processed
    outdir : str
        Output path directory
    label : str
        DB file name
    geolat : np.ma.masked_array
        Array of latitudes
    geolon : np.ma.masked_array
        Array of longitudes
    cell_area : np.ma.masked_array
        Array of cell areas
    area_types : dict, optional
        [description], by default None
    cell_depth : np.ma.masked_array, optional
        [description], by default None
    cell_frac : np.ma.masked_array, optional
        [description], by default None
    soil_area : np.ma.masked_array, optional
        [description], by default None
    soil_frac : np.ma.masked_array, optional
        [description], by default None
    average_dt : np.ma.masked_array
        Array of time averaging period
    """

    def __init__(
        self,
        varname,
        grid_file,
        data_file,
        fyear,
        outdir,
        label,
        geolat,
        geolon,
        cell_area,
        area_types=None,
        cell_depth=None,
        cell_frac=None,
        soil_area=None,
        soil_frac=None,
        average_dt=None,
    ):
        self.varname = varname
        self.grid_file = grid_file
        self.data_file = data_file
        self.fyear = fyear
        self.outdir = outdir
        self.label = label
        self.geolat = geolat
        self.geolon = geolon
        self.cell_area = cell_area
        self.area_types = area_types
        self.cell_depth = cell_depth
        self.cell_frac = cell_frac
        self.soil_area = soil_area
        self.soil_frac = soil_frac
        self.average_dt = average_dt

    def __str__(self):
        return self.__class__.__name__

    def __hash__(self):
        return hash([self.__dict__[x] for x in list(self.__dict__.keys())])
