from tempfile import NamedTemporaryFile
import pyhdfs
import pandas as pd
import psycopg2
from pyhive import hive
from pyhive.exc import DatabaseError
from schema.fit import ALL_TABLES
from schema.fit_aggregate import FIT_AGGREGATE_TABLES
from sqlalchemy import create_engine
from clickhouse_driver import Client    
import os

def extract_raw(table, BASE_PATH, RAW, ext_from=None, ext_to=None):
    hdfs_path = f"{BASE_PATH}{RAW}/{table}/"
    dest_file_name = f"{table}_01.snappy.parquet"
    hdfs_client = pyhdfs.HdfsClient(hosts="namenode:9870")

    db_params = {
        'dbname': 'postgres',
        'user': 'postgres.jiqnbdmcwjgalxzrgeji',
        'password': 'fit_iuh_khdl',
        'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    }

    db_uri = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}/{db_params['dbname']}"
    engine = create_engine(db_uri)

    extract_query = f"SELECT * FROM {table}"
    if ext_from and ext_to:
        extract_query = f"SELECT * FROM {table} WHERE updated_at BETWEEN '{ext_from}' and '{ext_to}';"
    
    # Use the SQLAlchemy engine in read_sql
    raw_df = pd.read_sql(extract_query, engine)

    # Validate and cast DataFrame schema
    def cast_column(df, column_name, column_type):
        if column_type == "BIGINT":
            return df[column_name].astype("Int64")  # Supports NaN as nullable integer
        elif column_type == "STRING":
            return df[column_name].astype(str)
        elif column_type == "BOOLEAN":
            return df[column_name].astype(bool)
        elif column_type == "DOUBLE":
            return df[column_name].astype(float)
        elif column_type == "TIMESTAMP":
            return pd.to_datetime(df[column_name], errors="coerce")
        else:
            raise ValueError(f"Unsupported column type: {column_type}")

    for col_schema in ALL_TABLES[table]["schema"]:
        col_name = col_schema['name']
        col_type = col_schema['type']
        if col_name in raw_df.columns:
            try:
                raw_df[col_name] = cast_column(raw_df, col_name, col_type)
            except Exception as e:
                raise ValueError(f"Error casting column '{col_name}' to type '{col_type}': {e}")

    # Writing to a temporary parquet file with Snappy compression
    temp_file = NamedTemporaryFile()
    raw_df.to_parquet(
        temp_file.name, 
        engine="pyarrow", 
        compression="snappy", 
        use_deprecated_int96_timestamps=True
    )

    # HDFS operations
    hdfs_client.delete(hdfs_path, recursive=True)
    if not hdfs_client.exists(hdfs_path):
        hdfs_client.mkdirs(hdfs_path)
    hdfs_client.copy_from_local(
        localsrc=temp_file.name,
        dest=hdfs_path + dest_file_name,
        overwrite=True,
        async_=True
    )
    temp_file.close()
    engine.dispose()  # Close the SQLAlchemy engine connection

def create_staging_table(table, BASE_PATH, RAW):
    connetion = hive.Connection(host='spark-thriftserver', port=10000)
    cursor = connetion.cursor()
    raw_table_name = f"default.{table}"
    cursor.execute(f"DROP TABLE IF EXISTS {raw_table_name}")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {raw_table_name} (
            {",".join(list(map(lambda col: f'{col["name"]} {col["type"]}', ALL_TABLES[table]["schema"])))}   
        )   
        STORED AS PARQUET
        LOCATION '{BASE_PATH}{RAW}/{table}/*.snappy.parquet'
    """)

    cursor.execute(f"ANALYZE TABLE {raw_table_name} COMPUTE STATISTICS")

def recreate_warehouse_table(table, BASE_PATH, WAREHOUSE):
    connetion = hive.Connection(host='spark-thriftserver', port=10000)
    cursor = connetion.cursor()
    warehouse_table_name = f"iceberg.warehouse.{table}"
    cursor.execute(f"DROP TABLE IF EXISTS {warehouse_table_name}")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS warehouse")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {warehouse_table_name} (
            {",".join(list(map(lambda col: f'{col["name"]} {col["type"]}', ALL_TABLES[table]["schema"])))}   
        )
        USING iceberg
        LOCATION '{BASE_PATH}{WAREHOUSE}/{table}/*.snappy.parquet'
    """)

def insert_warehouse_table(table):
    connetion = hive.Connection(host='spark-thriftserver', port=10000)
    cursor = connetion.cursor()
    raw_table_name = f"default.{table}"
    warehouse_table_name = f"iceberg.warehouse.{table}"
    count_query = f"SELECT COUNT(*) FROM {raw_table_name}"
    cursor.execute(count_query)
    has_staging_data = cursor.fetchone()[0]
    print(count_query, "---", has_staging_data)
    if has_staging_data == 0:
        print("STAGING HAS NO DATA, SKIPPING...")
    else:
        cursor.execute(f"""
            MERGE INTO {warehouse_table_name} t
            USING {raw_table_name} s
            ON {' AND '.join(list(map(lambda col_name: f"t.{col_name}=s.{col_name}", ALL_TABLES[table]["primary_key"])))}
            WHEN MATCHED 
                THEN UPDATE SET 
                {','.join(list(map(lambda col: f't.{col["name"]}=s.{col["name"]}', ALL_TABLES[table]["schema"])))}
            WHEN NOT MATCHED 
                THEN INSERT *
        """)

    
def aggregate_into_warehouse(table):
    cursor = hive.connect(host='spark-thriftserver', port=10000).cursor()
    cursor.execute("CREATE NAMESPACE IF NOT EXISTS iceberg.aggr_warehouse")
    cursor.execute(f"DROP TABLE IF EXISTS iceberg.aggr_warehouse.{table}")
    cursor.execute(FIT_AGGREGATE_TABLES[table]["create_table_command"])
    hdfs_client = pyhdfs.HdfsClient(hosts='namenode:9870')
    hdfs_client.delete(f"/user/hive/warehouse/aggr_warehouse.db/{table}_parquet", recursive=True)
    cursor.execute(f"""
        DROP TABLE IF EXISTS spark_catalog.aggr_warehouse.{table}_parquet
    """)
    cursor.execute(f"""
        CREATE TABLE spark_catalog.aggr_warehouse.{table}_parquet
        USING parquet
        AS
        SELECT * FROM iceberg.aggr_warehouse.{table}
    """)

def load_to_clickhouse(table, order_key):
    clickhouse_client = Client('clickhouse1', database="default")
    clickhouse_client.execute(f"""
        CREATE OR REPLACE TABLE {table}_hdfs
        ENGINE=HDFS('hdfs://namenode:9000/user/hive/warehouse/aggr_warehouse.db/{table}_parquet/*.snappy.parquet', 'Parquet')                          
    """)
    clickhouse_client.execute(f"""
        CREATE OR REPLACE TABLE {table} ON CLUSTER clickhouse_cluster
        AS {table}_hdfs
        ENGINE=MergeTree()
        ORDER BY ({order_key})    
        SETTINGS allow_nullable_key=true
    """)
    clickhouse_client.execute(f"""
        INSERT INTO {table} SELECT * FROM {table}_hdfs
    """)