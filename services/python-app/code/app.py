from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import os
from pathlib import Path
import io
import pandas as pd
import numpy as np
import math
import psycopg2
import pyhdfs
from datetime import datetime
from psycopg2.extras import execute_values
from tempfile import NamedTemporaryFile

app = FastAPI()

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

# Database connection parameters
DB_PARAMS = {
    'dbname': 'postgres',
    'user': 'postgres.jiqnbdmcwjgalxzrgeji',
    'password': 'fit_iuh_khdl',
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
}

# HDFS client configuration
HDFS_HOSTS = "namenode:9870"

# Allowed file extensions
ALLOWED_EXTENSIONS = {"csv", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx"}

def get_file_extension(filename: str) -> str:
    return filename.split(".")[-1].lower()


def sanitize_value(value):
    if isinstance(value, float) and math.isnan(value):
        return None  # or another default value
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value

def insert_data(table: str, file_content: bytes):
    """
    Insert data from CSV content into PostgreSQL and upload the file to HDFS.
    
    :param table: The table name corresponding to the data.
    :param file_content: The content of the CSV file as bytes.
    """
    # Establish PostgreSQL connection
    conn = psycopg2.connect(
        dbname=DB_PARAMS['dbname'],
        user=DB_PARAMS['user'],
        password=DB_PARAMS['password'],
        host=DB_PARAMS['host']
    )
    cursor = conn.cursor()

    # Initialize HDFS client
    hdfs_client = pyhdfs.HdfsClient(hosts=HDFS_HOSTS)

    try:
        # Read CSV data into DataFrame
        df = pd.read_csv(io.BytesIO(file_content))
        if df.empty:
            raise ValueError(f"File {table}.csv is empty.")

        # Replace NaN with None for SQL compatibility
        df = df.where(pd.notnull(df), None)

        # Prepare columns and placeholders
        columns = [col.replace(' ', '_').lower() for col in df.columns]
        cols_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        insert_query = f"INSERT INTO {table.lower()} ({cols_str}) VALUES %s ON CONFLICT DO NOTHING"

        # Convert DataFrame to list of tuples
        data = [tuple(sanitize_value(v) for v in row) for row in df.to_numpy()]

        # Execute batch insert
        execute_values(cursor, insert_query, data, template=f"({placeholders})", page_size=1000)

        # Commit the transaction
        conn.commit()

        # Define HDFS path
        hdfs_path = f"/data/raw/{table}/"
        if not hdfs_client.exists(hdfs_path):
            hdfs_client.mkdirs(hdfs_path)
        
        # Define destination file name with timestamp
        dest_file_name = f"{table}_{int(datetime.now().timestamp())}.csv"
        
        # Write file_content to a temporary file
        with NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            # Upload the temporary file to HDFS
            hdfs_client.copy_from_local(
                localsrc=tmp_path,
                dest=hdfs_path + dest_file_name,
                overwrite=True,
                async_=False  # Set to True if you want asynchronous upload
            )
        finally:
            # Ensure the temporary file is deleted after upload
            os.unlink(tmp_path)

    except Exception as e:
        print(f"Transaction failed for table {table}: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def extract_table_name(filename: str) -> str:
    # Sắp xếp danh sách theo độ dài giảm dần
    sorted_tables = sorted(ls_raw_tables, key=len, reverse=True)
    
    for table in sorted_tables:
        if table.lower() in filename.lower():
            return table
    raise ValueError(f"Filename '{filename}' does not contain a valid table name.")

@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Không có tệp tin nào được tải lên.")

    saved_files = []
    for file in files:
        ext = get_file_extension(file.filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Tệp tin {file.filename} có định dạng không được phép. Chỉ cho phép: {', '.join(ALLOWED_EXTENSIONS)}."
            )
        
        # Read the file content once
        file_content = await file.read()

        # Kiểm tra xem tệp tin thuộc bảng nào trong ls_raw_tables không? ví dụ: employee_13.csv -> employee
        # Lấy tên bảng từ tên tệp tin
        try:
            table = extract_table_name(file.filename)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        
        # Insert data into PostgreSQL and upload to HDFS
        try:
            insert_data(table, file_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process file {file.filename}: {str(e)}")
        
        # Lưu tên tệp tin đã tải lên
        saved_files.append(file.filename)

    return {"message": f"Đã tải lên thành công {len(saved_files)} tệp tin.", "files": saved_files}

# Serve static files from the 'static' directory
app.mount("/", StaticFiles(directory="static", html=True), name="static")