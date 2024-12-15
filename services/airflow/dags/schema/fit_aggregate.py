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
            SUM(CASE WHEN sf.final_score >= 4 THEN 1 ELSE 0 END) AS total_courses_passed,
            SUM(c.total_credit) AS total_credits_earned,
            ROUND(
                COALESCE(
                    SUM(CASE WHEN sf.final_score_4 >= 1 THEN sf.final_score_4 * c.total_credit ELSE 0 END) / 
                    NULLIF(SUM(CASE WHEN sf.final_score_4 >= 1 THEN c.total_credit ELSE 0 END), 0),
                    0
                ), 2) AS GPA
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
        {"name": "program_id", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "total_courses_enrolled", "type": "INT"},
        {"name": "total_courses_passed", "type": "INT"},
        {"name": "total_credits_earned", "type": "INT"},
        {"name": "GPA", "type": "DOUBLE"}
    ],
    "order_key": "GPA",
}

COURSE_PERFORMANCE = {
    "name": "course_performance",
    "create_table_command": """
    CREATE OR REPLACE TABLE iceberg.aggr_warehouse.course_performance
    USING parquet
    AS
    WITH unique_scores AS (
        SELECT
            c.course_code,
            c.course_name,
            ps.semester_name,
            sf.student_id,
            sf.final_score
        FROM
            iceberg.warehouse.course c
        JOIN iceberg.warehouse.instruction_fact inf 
            ON c.course_id = inf.course_id
        JOIN iceberg.warehouse.program_semester ps 
            ON inf.program_semester_id = ps.program_semester_id
        JOIN iceberg.warehouse.score_fact sf 
            ON sf.instruction_id = inf.instruction_id
        WHERE 
            inf.instruction_status = 'completed'
        GROUP BY
            c.course_code, c.course_name, ps.semester_name, sf.student_id, sf.final_score
    )
    SELECT
        course_code,
        course_name,
        semester_name,
        COUNT (student_id) AS num_students_enrolled,
        SUM(CASE WHEN final_score >= 4 THEN 1 ELSE 0 END) AS num_students_passed,
        (SUM(CASE WHEN final_score >= 4 THEN 1 ELSE 0 END) * 100.0) / COUNT(student_id) AS pass_rate,
        AVG(final_score) AS average_final_score
    FROM
        unique_scores
    GROUP BY
        course_code, course_name, semester_name;
    """,
    "schema": [
        {"name": "course_code", "type": "BIGINT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "num_students_enrolled", "type": "INT"},
        {"name": "num_students_passed", "type": "INT"},
        {"name": "pass_rate", "type": "DOUBLE"},
        {"name": "average_final_score", "type": "DOUBLE"}
    ],
    "order_key": "average_final_score",
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
    WHERE 
        inf.instruction_status = 'completed'
    GROUP BY
        l.lecturer_id,
        e.employee_name,
        c.course_id,
        c.course_name,
        ps.semester_name;
    """,
    "schema": [
        {"name": "lecturer_id", "type": "BIGINT"},  # Đã sửa từ INT thành BIGINT
        {"name": "lecturer_name", "type": "STRING"},
        {"name": "course_id", "type": "BIGINT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "num_classes_taught", "type": "INT"},
        {"name": "average_class_score", "type": "DOUBLE"}
    ],
    "order_key": "average_class_score",
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
    JOIN iceberg.warehouse.program_semester ps ON inf.program_semester_id = ps.program_semester_id
    WHERE 
        inf.instruction_status = 'completed';
    """,
    "schema": [
        {"name": "instruction_id", "type": "BIGINT"},  # Đã sửa từ INT thành BIGINT
        {"name": "course_id", "type": "BIGINT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "program_id", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "num_students", "type": "INT"},
        {"name": "avg_final_score", "type": "DOUBLE"}
    ],
    "order_key": "avg_final_score",
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
        ps.program_id,
        ps.semester_name,
        sf.academic_rank,
        COUNT(*) AS num_students_with_rank
    FROM
        iceberg.warehouse.score_fact sf
    JOIN iceberg.warehouse.instruction_fact inf 
        ON sf.instruction_id = inf.instruction_id
    JOIN iceberg.warehouse.course c 
        ON inf.course_id = c.course_id
    JOIN iceberg.warehouse.program_semester ps 
        ON inf.program_semester_id = ps.program_semester_id
    GROUP BY
        c.course_id,
        c.course_name,
        ps.program_id,
        ps.semester_name,
        sf.academic_rank;
    """,
    "schema": [
        {"name": "course_id", "type": "BIGINT"},
        {"name": "course_name", "type": "STRING"},
        {"name": "program_id", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "academic_rank", "type": "STRING"},
        {"name": "num_students_with_rank", "type": "INT"}
    ],
    "order_key": "num_students_with_rank",
}

STUDENT_PROGRAM_COMPLETION = {
    "name": "student_program_completion",
    "create_table_command": """
        CREATE OR REPLACE TABLE iceberg.aggr_warehouse.student_program_completion
        USING parquet
        AS
        WITH program_requirements AS (
            SELECT
                ps.program_id,
                SUM(ps.required_credit) AS total_required_credit,
                SUM(ps.elective_credit) AS total_elective_credit
            FROM
                iceberg.warehouse.program_semester ps
            GROUP BY
                ps.program_id
        ),
        student_courses AS (
            SELECT
                s.student_id,
                s.student_name,
                ps.program_id,
                ps.program_semester_id,
                COALESCE(SUM(CASE WHEN c.category = 'required' THEN c.total_credit ELSE 0 END), 0) AS total_required_credit_registered,
                COALESCE(SUM(CASE WHEN c.category = 'elective' THEN c.total_credit ELSE 0 END), 0) AS total_elective_credit_registered,
                COALESCE(SUM(CASE WHEN c.category = 'required' AND sf.final_score >= 4 THEN c.total_credit ELSE 0 END), 0) AS total_required_credit_passed,
                COALESCE(SUM(CASE WHEN c.category = 'elective' AND sf.final_score >= 4 THEN c.total_credit ELSE 0 END), 0) AS total_elective_credit_passed
            FROM
                iceberg.warehouse.student s
            JOIN iceberg.warehouse.enroll_student es ON s.student_id = es.student_id
            JOIN iceberg.warehouse.enrollment_fact ef ON es.enrollment_id = ef.enrollment_id
            JOIN iceberg.warehouse.instruction_fact inf ON ef.instruction_id = inf.instruction_id
            JOIN iceberg.warehouse.program_semester ps ON inf.program_semester_id = ps.program_semester_id
            JOIN iceberg.warehouse.course c ON inf.course_id = c.course_id
            LEFT JOIN iceberg.warehouse.score_fact sf ON sf.instruction_id = inf.instruction_id AND sf.student_id = s.student_id
            GROUP BY
                s.student_id,
                s.student_name,
                ps.program_id,
                ps.program_semester_id
        )
        SELECT
            sc.student_id,
            sc.student_name,
            sc.program_id,
            pr.total_required_credit,
            pr.total_elective_credit,
            SUM(sc.total_required_credit_registered) AS total_required_credit_registered,
            SUM(sc.total_elective_credit_registered) AS total_elective_credit_registered,
            SUM(sc.total_required_credit_passed) AS total_required_credit_passed,
            SUM(sc.total_elective_credit_passed) AS total_elective_credit_passed,
            CASE 
                WHEN SUM(sc.total_required_credit_registered) >= pr.total_required_credit
                     AND SUM(sc.total_elective_credit_registered) >= pr.total_elective_credit
                THEN 'Completed'
                ELSE 'Not Completed'
            END AS completion_status
        FROM
            student_courses sc
        JOIN program_requirements pr ON sc.program_id = pr.program_id
        GROUP BY
            sc.student_id,
            sc.student_name,
            sc.program_id,
            pr.total_required_credit,
            pr.total_elective_credit;
    """,
    "schema": [
        {"name": "student_id", "type": "STRING"},
        {"name": "student_name", "type": "STRING"},
        {"name": "program_id", "type": "STRING"},
        {"name": "total_required_credit", "type": "BIGINT"},
        {"name": "total_elective_credit", "type": "BIGINT"},
        {"name": "total_required_credit_registered", "type": "BIGINT"},
        {"name": "total_elective_credit_registered", "type": "BIGINT"},
        {"name": "total_required_credit_passed", "type": "BIGINT"},
        {"name": "total_elective_credit_passed", "type": "BIGINT"},
        {"name": "completion_status", "type": "STRING"}
    ],
    "order_key": "completion_status",
}

FIT_AGGREGATE_TABLES = {
    STUDENT_PERFORMANCE["name"]: STUDENT_PERFORMANCE,
    COURSE_PERFORMANCE["name"]: COURSE_PERFORMANCE,
    LECTURER_PERFORMANCE["name"]: LECTURER_PERFORMANCE,
    INSTRUCTION_AGGREGATE["name"]: INSTRUCTION_AGGREGATE,
    SCORE_DISTRIBUTION["name"]: SCORE_DISTRIBUTION,
    STUDENT_PROGRAM_COMPLETION["name"]: STUDENT_PROGRAM_COMPLETION
}