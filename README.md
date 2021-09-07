# pygeoapi-mssql-provider

Provider to add mssql containing spatial columns.

> NOTE: This package isn't tested against SQL injection. 

To install:
```commandline
pip install pygeoapi-mssql-provider
```

```yaml
providers:
  - type: feature
    name: pygeoapi_mssql_provider.mssql.MsSqlProvider
    data:                         # required group
      server: <SERVER>            # keywords correspond with pymssql `connect` method
      database: <DATABASE>
      user: <USERNAME>
      password: <PASSWORD>        
    id_field: <id_field>          # required field
    table: <table_name>           # required field
    geom_field: <geometry_field>  # required field
    source_srid: <srid>           # optional, will be retrieved if not specified
    target_srid: <srid>           # optional, only specify when you want to transform geometry
```
