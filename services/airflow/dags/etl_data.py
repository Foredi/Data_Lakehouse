import os
from datetime import datetime
from airflow import DAG
from airflow.decorators import dag, task_group, task
from tasks.etl_task import *
from airflow.operators.python_operator import PythonOperator

DAG_ID = "etl_data"
DAG_SCHEDULE = "0 0 1 6,8,12 *"

with DAG(
    DAG_ID,
    schedule=DAG_SCHEDULE,
    catchup=False,
    start_date=datetime.now(),
) as dag:
    ls_raw_tables = [
        "course",
        "program",
        "program_semester",
        "program_course",
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

    @task_group(group_id='insert_data')
    def insert_data_group():
        previous_task = None
        for table in ls_raw_tables:
            current_task = PythonOperator(
                task_id=f'insert_data_{table}',
                python_callable=insert_data,
                op_args=[BASE_PATH, RAW, table, False]
            )
            if previous_task:
                previous_task >> current_task
            previous_task = current_task
        
        # Task cuối cùng đổi tên thư mục
        rename_task = PythonOperator(
            task_id='rename_directories',
            python_callable=rename_directories,
            op_args=[BASE_PATH]
        )
        previous_task >> rename_task

    insert_data_group()