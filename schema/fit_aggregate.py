STUDENT_PERFORMANCE = {
    "name": "student_performance",
    "create_table_command": """
        CREATE OR REPLACE TABLE iceberg.aggr_warehouse.student_performance
        USING parquet
        AS
        SELECT
            s.student_id, 
            s.student_name, 
            ps.program_id, 
            ps.semester_name,
        COUNT(DISTINCT sf.score_id) AS total_courses_enrolled,
        SUM(CASE WHEN sf.final_score >= 5 THEN 1 ELSE 0 END) AS total_courses_passed,
        SUM(c.total_credit) AS total_credits_earned,
        AVG(sf.final_score) AS GPA
        FROM
            iceberg.warehouse.student s
        JOIN iceberg.warehouse.enroll_student es ON s.student_id = es.student_id
        JOIN iceberg.warehouse.enrollment_fact ef ON es.enrollment_id = ef.enrollment_id
        JOIN iceberg.warehouse.instruction_fact inf ON ef.instruction_id = inf.instruction_id
        JOIN iceberg.warehouse.program_semester ps ON inf.program_semester_id = ps.program_semester_id
        JOIN iceberg.warehouse.course c ON inf.course_id = c.course_id
        JOIN iceberg.warehouse.score_fact sf ON sf.instruction_id = inf.instruction_id AND sf.student_id = s.student_id
        GROUP BY
            s.student_id, 
            s.student_name, 
            ps.program_id, 
            ps.semester_name;
    """,
    "schema": [
        {"name": "student_id", "type": "STRING"},
        {"name": "student_name", "type": "STRING"},
        {"name": "program_id", "type": "INT"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "total_courses_enrolled", "type": "INT"},
        {"name": "total_courses_passed", "type": "INT"},
        {"name": "total_credits_earned", "type": "INT"},
        {"name": "GPA", "type": "DOUBLE"}
    ],
    "order_key": "student_id",
}

COURSE_PERFORMANCE = {
    "name": "course_performance",
    "create_table_command": """
    CREATE OR REPLACE TABLE iceberg.aggr_warehouse.course_performance
    USING parquet
    AS
    SELECT
        c.course_id,
        c.course_name,
        ps.semester_name,
    COUNT(DISTINCT sf.student_id) AS num_students_enrolled,
    SUM(CASE WHEN sf.final_score >= 5 THEN 1 ELSE 0 END) AS num_students_passed,
    (SUM(CASE WHEN sf.final_score >= 5 THEN 1 ELSE 0 END) * 100.0) / COUNT(DISTINCT sf.student_id) AS pass_rate,
    AVG(sf.final_score) AS average_final_score
    FROM
        iceberg.warehouse.course c
    JOIN iceberg.warehouse.instruction_fact inf ON c.course_id = inf.course_id
    JOIN iceberg.warehouse.program_semester ps ON inf.program_semester_id = ps.program_semester_id
    JOIN iceberg.warehouse.score_fact sf ON sf.instruction_id = inf.instruction_id
    GROUP BY
        c.course_id,
        c.course_name,
        ps.semester_name;
    """,
    "schema": [
        {"name": "course_id", "type": "INT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "num_students_enrolled", "type": "INT"},
        {"name": "num_students_passed", "type": "INT"},
        {"name": "pass_rate", "type": "DOUBLE"},
        {"name": "average_final_score", "type": "DOUBLE"}
    ],
    "order_key": "course_id",
}

LECTURER_PERFORMANCE = {
    "name": "lecturer_performance",
    "create_table_command": """
    CREATE OR REPLACE TABLE iceberg.aggr_warehouse.lecturer_performance
    USING parquet
    AS
    SELECT
        l.lecturer_id,
        e.employee_name AS lecturer_name,
        c.course_id,
        c.course_name,
        ps.semester_name,
    COUNT(DISTINCT inf.instruction_id) AS num_classes_taught,
    AVG(sf.final_score) AS average_class_score
    FROM
        iceberg.warehouse.lecturer l
    JOIN iceberg.warehouse.employee e ON l.employee_id = e.employee_id
    JOIN iceberg.warehouse.instruction_lecturer il ON l.lecturer_id = il.lecturer_id
    JOIN iceberg.warehouse.instruction_fact inf ON il.instruction_id = inf.instruction_id
    JOIN iceberg.warehouse.course c ON inf.course_id = c.course_id
    JOIN iceberg.warehouse.program_semester ps ON inf.program_semester_id = ps.program_semester_id
    JOIN iceberg.warehouse.score_fact sf ON sf.instruction_id = inf.instruction_id
    GROUP BY
        l.lecturer_id,
        e.employee_name,
        c.course_id,
        c.course_name,
        ps.semester_name;
    """,
    "schema": [
        {"name": "lecturer_id", "type": "INT"},
        {"name": "lecturer_name", "type": "STRING"},
        {"name": "course_id", "type": "INT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "num_classes_taught", "type": "INT"},
        {"name": "average_class_score", "type": "DOUBLE"}
    ],
    "order_key": "lecturer_id",
}

INSTRUCTION_AGGREGATE = {
    "name": "instruction_aggregate",
    "create_table_command": """
    CREATE OR REPLACE TABLE iceberg.aggr_warehouse.instruction_aggregate
    USING parquet
    AS
    SELECT
        inf.instruction_id,
        c.course_id,
        c.course_name,
        ps.program_id,
        ps.semester_name,
        inf.num_student AS num_students,
        inf.avg_final_score
    FROM
        iceberg.warehouse.instruction_fact inf
    JOIN iceberg.warehouse.course c ON inf.course_id = c.course_id
    JOIN iceberg.warehouse.program_semester ps ON inf.program_semester_id = ps.program_semester_id;
    """,
    "schema": [
        {"name": "instruction_id", "type": "INT"},
        {"name": "course_id", "type": "INT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "program_id", "type": "INT"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "num_students", "type": "INT"},
        {"name": "avg_final_score", "type": "DOUBLE"}
    ],
    "order_key": "instruction_id",
}

SCORE_DISTRIBUTION = {
    "name": "score_distribution",
    "create_table_command": """
    CREATE OR REPLACE TABLE iceberg.aggr_warehouse.score_distribution
    USING parquet
    AS
    SELECT
        c.course_id,
        c.course_name,
        ps.semester_name,
        CASE
            WHEN sf.final_score BETWEEN 0 AND 1 THEN '0-1'
            WHEN sf.final_score > 1 AND sf.final_score <= 2 THEN '1-2'
            WHEN sf.final_score > 2 AND sf.final_score <= 3 THEN '2-3'
            WHEN sf.final_score > 3 AND sf.final_score <= 4 THEN '3-4'
            ELSE 'Unknown'
        END AS score_range,
        COUNT(*) AS num_students_in_range
    FROM
        iceberg.warehouse.score_fact sf
    JOIN iceberg.warehouse.instruction_fact inf ON sf.instruction_id = inf.instruction_id
    JOIN iceberg.warehouse.course c ON inf.course_id = c.course_id
    JOIN iceberg.warehouse.program_semester ps ON inf.program_semester_id = ps.program_semester_id
    GROUP BY
        c.course_id,
        c.course_name,
        ps.semester_name,
        score_range;
    """,
    "schema": [
        {"name": "course_id", "type": "INT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "score_range", "type": "STRING"},
        {"name": "num_students_in_range", "type": "INT"}
    ],
    "order_key": "course_id",
}

FIT_AGGREGATE_TABLES = {
    STUDENT_PERFORMANCE["name"]: STUDENT_PERFORMANCE,
    COURSE_PERFORMANCE["name"]: COURSE_PERFORMANCE,
    LECTURER_PERFORMANCE["name"]: LECTURER_PERFORMANCE,
    INSTRUCTION_AGGREGATE["name"]: INSTRUCTION_AGGREGATE,
    SCORE_DISTRIBUTION["name"]: SCORE_DISTRIBUTION
}