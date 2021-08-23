import logging
from datetime import date, datetime

import pymssql
from shapely import wkt
from shapely.geometry import box, mapping

from .vendor import BaseProvider
from .vendor.provider_base import ProviderConnectionError, ProviderQueryError

LOGGER = logging.getLogger(__name__)


TYPES = {
    "bigint": int,
    "float": float,
    "int": int,
    "nvarchar": str,
    "varchar": str,
    "date": date,
    "datetime": datetime,
}


class DatabaseConnection:
    """Database connection class to be used as 'with' statement.
    The class returns a connection object.
    """

    def __init__(self, conn_dic, table, geometry_column, context="query"):
        """

        Parameters
        ----------
        conn_dic
        table
        context
        """

        self.conn_dic = conn_dic
        self.table = table
        self.context = context
        self.columns = None
        self.geometry_column = geometry_column
        self.fields = {}  # Dict of columns. Key is col name, value is type
        self.conn = None
        self.source_srid = None

    def __enter__(self):
        try:
            # rename dict keys to be compatible with pymssql
            self.conn_dic["server"] = self.conn_dic.pop("host")
            self.conn_dic["database"] = self.conn_dic.pop("dbname")

            self.conn = pymssql.connect(**self.conn_dic, charset="utf8")

        except pymssql.OperationalError:
            LOGGER.error(
                "Couldn't connect to SQL Server using:{}".format(str(self.conn_dic))
            )
            raise ProviderConnectionError()

        self.cur = self.conn.cursor(as_dict=True)

        if self.context == "query":
            # Getting columns
            query_cols = (
                "SELECT COLUMN_NAME, DATA_TYPE "
                "FROM information_schema.columns "
                "WHERE table_name = '{}' AND DATA_TYPE NOT IN ('geometry', 'geography')".format(
                    self.table
                )
            )

            self.cur.execute(query_cols)
            result = self.cur.fetchall()
            self.columns = ", ".join(item["COLUMN_NAME"] for item in result)

            query_srid = "SELECT {}.STSrid as srid FROM {}".format(
                self.geometry_column, self.table
            )
            self.cur.execute(query_srid)
            result_srid = self.cur.fetchone()
            self.srid = result_srid["srid"]

            self.fields = {
                row["COLUMN_NAME"]: {
                    "type": row["DATA_TYPE"],
                    "python_type": TYPES[row["DATA_TYPE"]],
                }
                for row in result
            }

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # some logic to commit/rollback
        self.conn.close()


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
        self.table = provider_def["table"]
        self.id_field = provider_def["id_field"]
        self.conn_dic = provider_def["data"]
        self.geom = provider_def.get("geom_field", "geom")
        self.source_srid = provider_def.get("source_srid")
        self.target_srid = provider_def.get("target_srid")

        LOGGER.debug("Setting Postgresql properties:")
        LOGGER.debug(
            "Connection String:{}".format(
                ",".join(("{}={}".format(*i) for i in self.conn_dic.items()))
            )
        )
        LOGGER.debug("Name:{}".format(self.name))
        LOGGER.debug("ID_field:{}".format(self.id_field))
        LOGGER.debug("Table:{}".format(self.table))

        LOGGER.debug("Get available fields/properties")

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
                if self.source_srid is None:
                    self.source_srid = db.source_srid

        return self.fields

    def __get_where_clauses(self, properties=[], bbox=[]):
        """
        Generates WHERE conditions to be implemented in query.
        Private method mainly associated with query method

        Parameters
        ----------
        properties : list of tuples (name, value)
        bbox : bounding box [minx, miny, maxx, maxy]

        Returns
        -------
        psycopg2.sql.Composed or psycopg2.sql.SQL
        """

        where_conditions = []
        if properties:
            property_clauses = ["{} = {}".format(k, v) for k, v in properties]
            where_conditions += property_clauses
        if bbox:
            bbox_wkt = box(bbox).wkt
            bbox_clause = "geometry::STGeomFromText({}, {}).STContains({})".format(
                bbox_wkt, self.source_srid, self.geom
            )
            where_conditions.append(bbox_clause)

        if where_conditions:
            return " WHERE {}".format(" AND ".join(where_conditions))
        else:
            return ""

    def query(
        self,
        startindex=0,
        limit=10,
        resulttype="results",
        bbox=[],
        datetime_=None,
        properties=[],
        sortby=[],
        select_properties=[],
        skip_geometry=False,
        q=None,
        **kwargs
    ):
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
        LOGGER.debug("Querying PostGIS")

        if resulttype == "hits":

            with DatabaseConnection(
                self.conn_dic, self.table, context="hits", geometry_column=self.geom
            ) as db:
                cursor = db.conn.cursor(as_dict=True)

                where_clause = self.__get_where_clauses(
                    properties=properties, bbox=bbox
                )
                sql_query = "SELECT COUNT(*) as hits from {} {}".format(
                    self.table, where_clause
                )
                try:
                    cursor.execute(sql_query)
                except Exception as err:
                    LOGGER.error(
                        "Error executing sql_query: {}: {}".format(sql_query, err)
                    )
                    raise ProviderQueryError()

                hits = cursor.fetchone()["hits"]

            return self.__response_feature_hits(hits)

        end_index = startindex + limit

        with DatabaseConnection(
            self.conn_dic, self.table, geometry_column=self.geom
        ) as db:
            cursor = db.conn.cursor(as_dict=True)

            where_clause = self.__get_where_clauses(properties=properties, bbox=bbox)

            sql_query = 'SELECT {}, {}.STAsText() FROM {}{}'.format(
                db.columns, self.geom, self.table, where_clause
            )

            LOGGER.debug("SQL Query: {}".format(sql_query))
            LOGGER.debug("Start Index: {}".format(startindex))
            LOGGER.debug("End Index: {}".format(end_index))
            try:
                cursor.execute(sql_query)
                for index in [startindex, limit]:
                    cursor.execute("fetch forward {} from geo_cursor".format(index))
            except Exception as err:
                LOGGER.error(
                    "Error executing sql_query: {}".format(sql_query.as_string(cursor))
                )
                LOGGER.error(err)
                raise ProviderQueryError()

            row_data = cursor.fetchall()

            feature_collection = {"type": "FeatureCollection", "features": []}

            for rd in row_data:
                feature_collection["features"].append(self.__response_feature(rd))

            return feature_collection

    def get(self, identifier):
        pass

    def create(self, new_feature):
        pass

    def update(self, identifier, new_feature):
        pass

    def __response_feature(self, row_data):
        """
        Assembles GeoJSON output from DB query
        Parameters
        ----------
        row_data : DB row result

        Returns
        -------
        `dict` of GeoJSON Feature
        """
        if row_data:
            feature = {
                'type': 'Feature'
            }

            geom = mapping(wkt.loads(row_data.pop("geometry")))

            feature['geometry'] = geom if geom is not None else None  # noqa

            feature['properties'] = row_data
            feature['id'] = feature['properties'].get(self.id_field)

            return feature
        else:
            return None

    def __response_feature_hits(self, hits):
        """Assembles GeoJSON/Feature number
        e.g: http://localhost:5000/collections/
        hotosm_bdi_waterways/items?resulttype=hits
        :returns: GeoJSON FeaturesCollection
        """

        return {"features": [], "type": "FeatureCollection", "numberMatched": hits}
