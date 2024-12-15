import os
from datetime import datetime
from airflow import DAG
from airflow.decorators import dag, task_group, task
from tasks.etl_task import *
from airflow.operators.python_operator import PythonOperator

DAG_ID = "migration_fit_schema"
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
        "program_course",
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
    BASE_PATH = 'data'
    RAW = "raw"

    @task_group(group_id='create_table')
    def create_table_group():
        create_table_task = PythonOperator(
            task_id='create_table',
            python_callable=create_table,
            op_args=[BASE_PATH, RAW]
        )
        create_table_task

    @task_group(group_id='insert_data')
    def insert_data_group():
        previous_task = None
        for table in ls_raw_tables:
            current_task = PythonOperator(
                task_id=f'insert_data_{table}',
                python_callable=insert_data,
                op_args=[BASE_PATH, RAW, table, True]
            )
            if previous_task:
                previous_task >> current_task
            previous_task = current_task

    # Gọi nhóm task ngay trong dag
    create_table_group() >> insert_data_group()