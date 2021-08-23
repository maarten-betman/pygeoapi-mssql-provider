import pytest

from pygeoapi_mssql_provider.mssql import MsSqlProvider, DatabaseConnection


@pytest.fixture()
def config():
    return {
        "name": "SQLServer",
        "type": "feature",
        "data": {
            "host": "10.64.32.62",
            "dbname": "test_engdep",
            "user": "api",
            "password": "api",
        },
        "id_field": "ID",
        "table": "BOX",
        "geom_field": "GEOM",
        "srid": 3414,
    }


def test_database_connection(config):
    with DatabaseConnection(config["data"], config["table"], geometry_column=config['geom_field']) as db:
        fields = db.fields
        srid = db.srid
    assert isinstance(fields, dict)
    assert srid == config["srid"]
