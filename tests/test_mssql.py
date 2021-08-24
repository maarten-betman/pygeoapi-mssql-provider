import pytest

from pygeoapi_mssql_provider.mssql import MsSqlProvider, DatabaseConnection
from pygeoapi_mssql_provider.log import setup_logger
from pygeoapi_mssql_provider.vendor.provider_base import ProviderItemNotFoundError

setup_logger({"level": "DEBUG"})


@pytest.fixture()
def config():
    return {
        "name": "SQLServer",
        "type": "feature",
        "data": {
            "server": "10.64.32.62",
            "database": "test_engdep",
            "user": "api",
            "password": "api",
        },
        "id_field": "ID",
        "table": "POINT",
        "geom_field": "GEOM",
        "source_srid": 3414,
    }


def test_database_connection(config):
    with DatabaseConnection(
        config["data"], config["table"], geometry_column=config["geom_field"]
    ) as db:
        fields = db.fields
        srid = db.source_srid
    assert isinstance(fields, dict)
    assert srid == config["source_srid"]


def test_query(config):
    p = MsSqlProvider(config)
    feature_collection = p.query()
    assert isinstance(feature_collection, dict)
    assert feature_collection.get("type", None) == "FeatureCollection"
    features = feature_collection.get("features", None)
    assert features is not None
    feature = features[0]
    properties = feature.get("properties", None)
    assert properties is not None
    geometry = feature.get("geometry", None)
    assert geometry is not None


def test_query_with_property(config):
    p = MsSqlProvider(config)
    feature_collection = p.query(properties=[("Box", "ZB41")])
    features = feature_collection.get("features", None)
    stream_features = list(
        filter(lambda feature: feature["properties"]["Box"] == "ZB41", features)
    )
    assert len(features) == len(stream_features)

    feature_collection = p.query(properties=[("ID", 139)])
    features = feature_collection.get("features", None)
    stream_features = list(
        filter(lambda feature: feature["properties"]["PointID"] == "ABH-15", features)
    )
    assert len(features) == len(stream_features)


def test_query_bbox(config):
    """Test query with a specified bounding box"""
    psp = MsSqlProvider(config)
    boxed_feature_collection = psp.query(bbox=[49662.6, 46395.4, 49697.0, 46424.1])
    assert len(boxed_feature_collection["features"]) == 5


def test_get(config):
    """Testing query for a specific object"""
    p = MsSqlProvider(config)
    result = p.get(2293)
    assert isinstance(result, dict)
    assert "geometry" in result
    assert "properties" in result
    assert "id" in result
    assert "CPT-306" in result["properties"]["PointID"]


def test_get_not_existing_item_raise_exception(config):
    """Testing query for a not existing object"""
    p = MsSqlProvider(config)
    with pytest.raises(ProviderItemNotFoundError):
        p.get(-1)


def test_coordinate_transfrom(config):
    config["target_srid"] = 4326
    p = MsSqlProvider(config)
    result = p.get(4053)
    assert "CPT-352" in result["properties"]["PointID"]
    assert (104.0266684895768, 1.4295970427024443) == result["geometry"]["coordinates"]
