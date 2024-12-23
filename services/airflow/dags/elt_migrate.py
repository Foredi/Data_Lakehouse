import os
from datetime import datetime
from airflow import DAG
import pandas
from tempfile import NamedTemporaryFile
import pyhdfs
from pyhive import hive
import subprocess
from airflow.decorators import dag, task_group, task
from schema.fit import ALL_TABLES
from schema.fit_aggregate import FIT_AGGREGATE_TABLES
from pyhive.exc import Error
from clickhouse_driver import Client
from tasks.fit_task import *
from airflow.operators.python_operator import PythonOperator

DAG_ID = "migration_fit_data"
DAG_SCHEDULE = None
with DAG(
    DAG_ID,
    schedule=DAG_SCHEDULE,
    catchup=False,
    # start_date=datetime(2024, 1, 1),
) as dag:
    ls_raw_tables = [
        "employee",
        "lecturer",
        "course",
        "program",
        "program_semester",
        # "program_course",
        "class",
        "address",
        "student",
        "instruction_fact",
        "instruction_lecturer",
        "enrollment_fact",
        "enroll_student",
        "score_fact",
        "score_detail"
    ]
    BASE_PATH = '/fit_warehouse'
    RAW = "/raw"
    WAREHOUSE = "/warehouse"
    @task_group(group_id='get_raw_data')
    def taskgr_get_raw_data():
        for table in ls_raw_tables:
            extract_raw_task = PythonOperator(
                task_id=f'extract_raw_{table}',
                python_callable=extract_raw,
                op_args=[table, BASE_PATH, RAW]
            )
            extract_raw_task
    
    @task_group(group_id='load_staging')
    def load_staging():
        for table in ls_raw_tables:
            create_staging_task = PythonOperator(
                task_id=f'create_staging_{table}',
                python_callable=create_staging_table,
                op_args=[table, BASE_PATH, RAW]
            )
            create_staging_task
            
    @task_group(group_id='create_dwh_table')
    def create_datawarehouse_table():
        for table in ls_raw_tables:
            recreate_warehouse_table_task = PythonOperator(
                task_id=f"recreate_dwh_{table}",
                python_callable=recreate_warehouse_table,
                op_args=[table, BASE_PATH, WAREHOUSE]
            )
            recreate_warehouse_table_task
         
    @task_group(group_id='insert_warehouse')        
    def insert_into_warehouse():
        for table in ls_raw_tables:
            insert_warehouse_table_task = PythonOperator(
                task_id=f"insert_dwh_{table}",
                python_callable=insert_warehouse_table,
                op_args=[table]
            )
            insert_warehouse_table_task
            
    @task_group(group_id='aggregate_warehouse')        
    def aggregate_warehouse():
        for table in FIT_AGGREGATE_TABLES:
            aggregate_into_warehouse_task = PythonOperator(
                task_id=f"aggregate_{table}",
                python_callable=aggregate_into_warehouse,
                op_args=[table]
            )
            aggregate_into_warehouse_task
            
    @task_group(group_id='load_to_clickhouse')        
    def taskgr_load_to_clickhouse():
        for table in FIT_AGGREGATE_TABLES:
            load_to_clickhouse_task = PythonOperator(
                task_id=f"load_clickhouse_{table}",
                python_callable=load_to_clickhouse,
                op_args=[table, FIT_AGGREGATE_TABLES[table]["order_key"]]
            )
            load_to_clickhouse_task
            
    taskgr_get_raw_data() >> load_staging() >> create_datawarehouse_table() >> insert_into_warehouse() >> aggregate_warehouse() >> taskgr_load_to_clickhouse()