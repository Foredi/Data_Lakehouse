import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
import pyhdfs
import os
import re
import glob
import math
import numpy as np
from datetime import datetime

def sanitize_value(value):
    if isinstance(value, float) and math.isnan(value):
        return None  # hoặc một giá trị mặc định khác
    if isinstance(value, np.integer):  # Nếu là số nguyên (integer)
        return int(value)  # Trả về kiểu int
    if isinstance(value, np.floating):  # Nếu là số thực (floating-point)
        return float(value)  # Trả về kiểu float
    return value

def create_table(BASE_PATH, RAW):
    db_params = {
        'dbname': 'postgres',
        'user': 'postgres.jiqnbdmcwjgalxzrgeji',
        'password': 'fit_iuh_khdl',
        'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    }
    # Create SQLAlchemy engine with the database URI
    db_uri = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}/{db_params['dbname']}"
    engine = create_engine(db_uri)

    # read file create_table.sql
    
    create_table_sql_path = os.path.join("/opt/airflow/dags/", BASE_PATH, RAW, "create_table.sql")
    with open(create_table_sql_path, 'r') as f:
        create_table_sql = f.read()

    # Execute the CREATE TABLE SQL statement
    with engine.begin() as conn:
        conn.execute(text(create_table_sql))

def insert_data(BASE_PATH, RAW, table, migrate=False):
    db_params = {
        'dbname': 'postgres',
        'user': 'postgres.jiqnbdmcwjgalxzrgeji',
        'password': 'fit_iuh_khdl',
        'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    }

    # Kết nối đến PostgreSQL
    conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host']
    )
    cursor = conn.cursor()

    hdfs_client = pyhdfs.HdfsClient(hosts="namenode:9870")

    try:
        # Xác định đường dẫn file CSV
        if migrate:
            csv_path = os.path.join("/opt/airflow/dags/", BASE_PATH, RAW, f"{table}.csv")
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Không tìm thấy file {table}.csv tại {csv_path}")
        else:
            current_dirs = glob.glob(os.path.join("/opt/airflow/dags/", BASE_PATH, "K*_current"))
            if len(current_dirs) == 0:
                raise FileNotFoundError("Không tìm thấy thư mục Kxx_current nào.")
            
            if len(current_dirs) > 1:
                raise Exception("Tồn tại nhiều hơn một thư mục Kxx_current, không rõ thư mục cần xử lý.")

            current_dir = current_dirs[0]
            match = re.search(r"K(\d+)_current$", os.path.basename(current_dir))
            if not match:
                raise ValueError("Tên thư mục không đúng định dạng Kxx_current.")
            
            current_number = int(match.group(1))
            csv_path = os.path.join(current_dir, f"{table}.csv")
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Không tìm thấy file {table}.csv trong thư mục {current_dir}")

        # Đọc dữ liệu CSV
        df = pd.read_csv(csv_path)
        if df.empty:
            raise ValueError(f"File {table}.csv rỗng.")

        # Thay NaN bằng None để phù hợp với NULL trong SQL
        df = df.where(pd.notnull(df), None)

        # Chuẩn bị câu lệnh INSERT
        columns = [col.replace(' ', '_').lower() for col in df.columns]
        cols_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        insert_query = f"INSERT INTO {table.lower()} ({cols_str}) VALUES %s ON CONFLICT DO NOTHING"

        # Chuyển DataFrame thành list tuple để phù hợp với execute_values
        data = [tuple(row) for row in df.to_numpy()]

        data = [tuple(sanitize_value(v) for v in row) for row in data]

        # Thực hiện các thao tác liên quan đến việc chèn dữ liệu
        execute_values(cursor, insert_query, data, template=f"({placeholders})", page_size=1000)

        # Commit dữ liệu
        conn.commit()

        hdfs_path = f"/{BASE_PATH}/{RAW}/{table}/"
        if not hdfs_client.exists(hdfs_path):
            hdfs_client.mkdirs(hdfs_path)
        dest_file_name = f"{table}_{int(datetime.now().timestamp())}.csv"
        hdfs_client.copy_from_local(
            localsrc=csv_path,
            dest=hdfs_path + dest_file_name,
            overwrite=True,
            async_=True
        )
    except Exception as e:
        print(f"Transaction failed for table {table}: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def rename_directories(BASE_PATH):
    search_pattern = os.path.join("/opt/airflow/dags/", BASE_PATH, "K*_current")
    current_dirs = glob.glob(search_pattern)
    
    if len(current_dirs) == 0:
        raise FileNotFoundError("Không tìm thấy thư mục Kxx_current nào.")
    
    if len(current_dirs) > 1:
        raise Exception("Tồn tại nhiều hơn một thư mục Kxx_current, không rõ thư mục cần xử lý.")
    
    current_dir = current_dirs[0]
    base_name = os.path.basename(current_dir)
    match = re.search(r"K(\d+)_current$", base_name)
    
    if not match:
        raise ValueError("Tên thư mục không đúng định dạng Kxx_current.")
    
    current_number = int(match.group(1))
    parent_dir = os.path.dirname(current_dir)
    
    # Define the new name for the current directory
    new_dir = os.path.join(parent_dir, f"K{current_number}")
    
    if os.path.exists(new_dir):
        raise FileExistsError(f"Thư mục {new_dir} đã tồn tại, không thể đổi tên.")
    
    # Rename current directory
    os.rename(current_dir, new_dir)
    print(f"Đổi tên thư mục {current_dir} thành {new_dir}")
    
    # Define the next directory's expected names
    next_dir = os.path.join(parent_dir, f"K{current_number + 1}")
    next_dir_current = os.path.join(parent_dir, f"K{current_number + 1}_current")
    
    if os.path.exists(next_dir):
        if os.path.exists(next_dir_current):
            raise FileExistsError(f"Thư mục {next_dir_current} đã tồn tại, không thể đổi tên.")
        # Rename next directory
        os.rename(next_dir, next_dir_current)
        print(f"Đổi tên thư mục {next_dir} thành {next_dir_current}")
    else:
        # Next directory does not exist; skip renaming
        print(f"Thư mục tiếp theo {next_dir} không tồn tại. Bỏ qua việc đổi tên.")
    