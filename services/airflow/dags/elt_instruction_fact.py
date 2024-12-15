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
from airflow.utils.session import create_session
from airflow.models import DagRun
from airflow.models.taskinstance import TaskInstance
from airflow.utils.state import State
import logging

def get_latest_dag_execution_date(dag_id):
    with create_session() as session:
        latest_run = session.query(DagRun).filter(
            DagRun.dag_id == dag_id,
            DagRun.state == State.SUCCESS
        ).order_by(DagRun.execution_date.desc())
        result = latest_run.first()
        if result:
            logging.info(f"Found latest execution date for {dag_id}: {result.execution_date}")
            return result.execution_date
        else:
            logging.warning(f"No successful runs found for DAG {dag_id}")
            return None

DAG_ID = "etl_instruction_fact_data"
MIGRATION_DAG_ID = "migration_fit_data"
DAG_SCHEDULE = "0 0 1 * *"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Lấy thời gian từ DAG phù hợp
ext_from = get_latest_dag_execution_date(dag_id=DAG_ID)
if ext_from:
    ext_from = ext_from.strftime(DATETIME_FORMAT)
else:
    # Nếu DAG chưa từng chạy, lấy thời gian từ migration_fit_data
    ext_from = get_latest_dag_execution_date(dag_id=MIGRATION_DAG_ID)
    if ext_from:
        ext_from = ext_from.strftime(DATETIME_FORMAT)
    else:
        # Nếu cả hai DAG chưa từng chạy, sử dụng thời gian mặc định
        ext_from = datetime.now().strftime(DATETIME_FORMAT) 
ext_to = datetime.now().strftime(DATETIME_FORMAT)
with DAG(
    DAG_ID,
    schedule=DAG_SCHEDULE,
    catchup=False,
    max_active_runs=1,
    start_date=datetime.now()
) as dag:
    ls_raw_tables = [
        "instruction_fact",
        "instruction_lecturer",
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
                op_args=[table, BASE_PATH, RAW, ext_from, ext_to]
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
            
    taskgr_get_raw_data() >> load_staging() >> insert_into_warehouse() >> aggregate_warehouse() >> taskgr_load_to_clickhouse()