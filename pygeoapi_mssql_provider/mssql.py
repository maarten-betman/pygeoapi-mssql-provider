import logging
from vendor import BaseProvider


LOGGER = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self, conn_dic, table, context="query"):
        """"""


class MsSqlProvider(BaseProvider):

    def __init__(self, provider_def: dict):
        """
        MsSqlProvider Class constructor

        Parameters
        ----------
        provider_def : dict
            provider definitions from yml pygeoapi-config.
            data,id_field, name set in parent class
            data contains the connection information
            for class DatabaseCursor

        Returns
        -------
        pygeoapi_mssql_provider.mssql.MsSqlProvidor
        """

        super().__init__(provider_def)
        self.table = provider_def['table']
        self.id_field = provider_def['id_field']
        self.conn_dic = provider_def['data']
        self.geom = provider_def.get('geom_field', 'geom')

        LOGGER.debug('Setting Postgresql properties:')
        LOGGER.debug('Connection String:{}'.format(
            ",".join(("{}={}".format(*i) for i in self.conn_dic.items()))))
        LOGGER.debug('Name:{}'.format(self.name))
        LOGGER.debug('ID_field:{}'.format(self.id_field))
        LOGGER.debug('Table:{}'.format(self.table))

        LOGGER.debug('Get available fields/properties')

        self.get_fields()

    def get_fields(self):
        """
        Get fields from PostgreSQL table (columns are field)

        Returns
        -------
        dict of fields
        """
        if not self.fields:
            with DatabaseConnection(self.conn_dic, self.table) as db:
                self.fields = db.fields
        return self.fields

    def get_data_path(self, baseurl, urlpath, dirpath):
        pass

    def get_metadata(self):
        pass

    def query(self, startindex=0, limit=10, resulttype='results',
              bbox=[], datetime_=None, properties=[], sortby=[],
              select_properties=[], skip_geometry=False, q=None, **kwargs):
        """
        Query MSSQL for all the content.
        e,g: http://localhost:5000/collections/hotosm_bdi_waterways/items?
        limit=1&resulttype=results

        Parameters
        ----------
        startindex : int
            starting record to return (default 0)
        limit : int
            number of records to return (default 10)
        resulttype : str
            return results or hit limit (default results)
        bbox : list(float)
            bounding box [minx,miny,maxx,maxy]
        datetime_ : datetime
            temporal (datestamp or extent)
        properties : Iterable
            list of tuples (name, value)
        sortby : List[dict]
            list of dicts (property, order)
        select_properties : List
            list of property names
        skip_geometry : bool
            bool of whether to skip geometry (default False)
        q : str
            full-text search term(s)
        kwargs : kwargs
            not passed down at the moment

        Returns
        -------
        GeoJSON FeaturesCollection

        """
        pass

    def get(self, identifier):
        pass

    def create(self, new_feature):
        pass

    def update(self, identifier, new_feature):
        pass

    def get_coverage_domainset(self):
        pass

    def get_coverage_rangetype(self):
        pass

    def delete(self, identifier):
        pass
