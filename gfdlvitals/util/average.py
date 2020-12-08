""" Utiliites for use in averaging routines """

__all__ = ["RichVariable"]


class RichVariable:
    """Metadata-rich variable class"""

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
        """[summary]

        Parameters
        ----------
        varname : [type]
            [description]
        grid_file : [type]
            [description]
        data_file : [type]
            [description]
        fyear : [type]
            [description]
        outdir : [type]
            [description]
        label : [type]
            [description]
        geolat : [type]
            [description]
        geolon : [type]
            [description]
        cell_area : [type]
            [description]
        area_types : [type], optional
            [description], by default None
        cell_depth : [type], optional
            [description], by default None
        cell_frac : [type], optional
            [description], by default None
        soil_area : [type], optional
            [description], by default None
        soil_frac : [type], optional
            [description], by default None
        area_types : dict
            Dictionary of different land area types
        cell_depth : np.ma.masked_array
            Array of cell depths
        average_dt : np.ma.masked_array
            Array of time averaging period
        """
        self.varname = varname
        self.grid_file = grid_file
        self.data_file = data_file
        self.fyear = fyear
        self.outdir = outdir
        self.label = label
        self.geolat = geolat
        self.geolon = geolon
        self.cell_area = cell_area
        self.cell_area = cell_area
        self.cell_area = cell_area
        self.cell_frac = cell_frac
        self.soil_area = soil_area
        self.soil_frac = soil_frac
        self.average_dt = average_dt

    def __str__(self):
        return self.__class__.__name__

    def __hash__(self):
        return hash([self.__dict__[x] for x in list(self.__dict__.keys())])
