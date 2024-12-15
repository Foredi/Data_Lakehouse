EMPLOYEE = {
    "name": "employee",
    "schema": [
        {"name": "employee_id", "type": "BIGINT", "primary_key": True},
        {"name": "employee_name", "type": "STRING"},
        {"name": "day_of_birth", "type": "TIMESTAMP"},
        {"name": "nationality", "type": "STRING"},
        {"name": "insurance_id", "type": "STRING"}
    ],
    "primary_key": ["employee_id"],
    "foreign_key": [],
    "table_type": "dim",
}

LECTURER = {
    "name": "lecturer",
    "schema": [
        {"name": "lecturer_id", "type": "BIGINT", "primary_key": True},
        {"name": "employee_id", "type": "BIGINT"},
        {"name": "academic_title", "type": "STRING"},
        {"name": "academic_title_date", "type": "TIMESTAMP"},
        {"name": "degree", "type": "STRING"},
        {"name": "degree_issue_date", "type": "TIMESTAMP"},
        {"name": "degree_issue_place", "type": "STRING"},
        {"name": "major", "type": "STRING"},
        {"name": "department", "type": "STRING"},
        {"name": "number_of_exp", "type": "BIGINT"}
    ],
    "primary_key": ["lecturer_id"],
    "foreign_key": [
        {"column": "employee_id", "reference": {"table": "employee", "column": "employee_id"}}
    ],
    "table_type": "dim",
}

PROGRAM = {
    "name": "program",
    "schema": [
        {"name": "program_id", "type": "STRING", "primary_key": True},
        {"name": "class_of", "type": "STRING"}
    ],
    "primary_key": ["program_id"],
    "foreign_key": [],
    "table_type": "dim",
}

PROGRAM_SEMESTER = {
    "name": "program_semester",
    "schema": [
        {"name": "program_semester_id", "type": "BIGINT", "primary_key": True},
        {"name": "program_id", "type": "STRING"},
        {"name": "semester_name", "type": "STRING"},
        {"name": "total_credit", "type": "BIGINT"},
        {"name": "required_credit", "type": "BIGINT"},
        {"name": "elective_credit", "type": "BIGINT"}
    ],
    "primary_key": ["program_semester_id"],
    "foreign_key": [
        {"column": "program_id", "reference": {"table": "program", "column": "program_id"}}
    ],
    "table_type": "dim",
}

COURSE = {
    "name": "course",
    "schema": [
        {"name": "course_id", "type": "BIGINT", "primary_key": True},
        {"name": "course_name", "type": "STRING"},
        {"name": "course_code", "type": "BIGINT"},
        {"name": "category", "type": "STRING"},
        {"name": "total_credit", "type": "BIGINT"},
        {"name": "theory_credit", "type": "BIGINT"},
        {"name": "practice_credit", "type": "BIGINT"},
        {"name": "self_learning_credit", "type": "BIGINT"}
    ],
    "primary_key": ["course_id"],
    "foreign_key": [],
    "table_type": "dim",
}

CLASS = {
    "name": "class",
    "schema": [
        {"name": "class_id", "type": "BIGINT", "primary_key": True},
        {"name": "class_name", "type": "STRING"},
        {"name": "last_modified_date", "type": "TIMESTAMP"}
    ],
    "primary_key": ["class_id"],
    "foreign_key": [],
    "table_type": "dim",
}

ADDRESS = {
    "name": "address",
    "schema": [
        {"name": "address_id", "type": "BIGINT", "primary_key": True},
        {"name": "ward", "type": "STRING"},
        {"name": "district", "type": "STRING"},
        {"name": "city", "type": "STRING"}
    ],
    "primary_key": ["address_id"],
    "foreign_key": [],
    "table_type": "dim",
}

STUDENT = {
    "name": "student",
    "schema": [
        {"name": "student_id", "type": "STRING", "primary_key": True},
        {"name": "student_name", "type": "STRING"},
        {"name": "class_name", "type": "STRING"},
        {"name": "edu_mail", "type": "STRING"},
        {"name": "address_id", "type": "BIGINT"},
        {"name": "national_id", "type": "BIGINT"},
        {"name": "key_year", "type": "STRING"},
        {"name": "gender", "type": "STRING"},
        {"name": "student_dob", "type": "TIMESTAMP"}
    ],
    "primary_key": ["student_id"],
    "foreign_key": [
        {"column": "address_id", "reference": {"table": "address", "column": "address_id"}}
    ],
    "table_type": "dim",
}

INSTRUCTION = {
    "name": "instruction_fact",
    "schema": [
        {"name": "instruction_id", "type": "BIGINT", "primary_key": True},
        {"name": "program_semester_id", "type": "BIGINT"},
        {"name": "course_id", "type": "BIGINT"},
        {"name": "class_id", "type": "BIGINT"},
        {"name": "is_required", "type": "BOOLEAN"},
        {"name": "num_student", "type": "BIGINT"},
        {"name": "num_pass_student", "type": "BIGINT"},
        {"name": "num_fail_student", "type": "BIGINT"},
        {"name": "avg_final_score", "type": "DOUBLE"},
        {"name": "instruction_status", "type": "STRING"},
        {"name": "instruction_allocate", "type": "TIMESTAMP"},
        {"name": "instruction_time_start", "type": "TIMESTAMP"},
        {"name": "instruction_time_end", "type": "TIMESTAMP"},
        {"name": "last_modified_date", "type": "TIMESTAMP"},
        {"name": "etl_date", "type": "TIMESTAMP"}
    ],
    "primary_key": ["instruction_id"],
    "foreign_key": [
        {"column": "program_semester_id", "reference": {"table": "program_semester", "column": "program_semester_id"}},
        {"column": "course_id", "reference": {"table": "course", "column": "course_id"}},
        {"column": "class_id", "reference": {"table": "class", "column": "class_id"}}
    ],
    "table_type": "fact",
}

INSTRUCTION_LECTURER = {
    "name": "instruction_lecturer",
    "schema": [
        {"name": "instruction_lecturer_id", "type": "BIGINT", "primary_key": True},
        {"name": "instruction_id", "type": "BIGINT"},
        {"name": "lecturer_id", "type": "BIGINT"},
        {"name": "lecturer_type", "type": "STRING"}
    ],
    "primary_key": ["instruction_lecturer_id"],
    "foreign_key": [
        {"column": "instruction_id", "reference": {"table": "instruction_fact", "column": "instruction_id"}},
        {"column": "lecturer_id", "reference": {"table": "lecturer", "column": "lecturer_id"}}
    ],
    "table_type": "fact",
}

ENROLLMENT = {
    "name": "enrollment_fact",
    "schema": [
        {"name": "enrollment_id", "type": "BIGINT", "primary_key": True},
        {"name": "instruction_id", "type": "BIGINT"},
        {"name": "enrollment_start_time", "type": "TIMESTAMP"},
        {"name": "enrollment_end_time", "type": "TIMESTAMP"},
        {"name": "enrollment_class", "type": "STRING"},
        {"name": "enrollment_status", "type": "STRING"},
        {"name": "last_modified_date", "type": "TIMESTAMP"},
        {"name": "etl_date", "type": "TIMESTAMP"}
    ],
    "primary_key": ["enrollment_id"],
    "foreign_key": [
        {"column": "instruction_id", "reference": {"table": "instruction_fact", "column": "instruction_id"}}
    ],
    "table_type": "fact",
}

ENROLL_STUDENT = {
    "name": "enroll_student",
    "schema": [
        {"name": "student_id", "type": "STRING"},
        {"name": "enrollment_id", "type": "BIGINT"},
        {"name": "enrollment_time", "type": "TIMESTAMP"},
    ],
    "primary_key": ["student_id", "enrollment_id"],
    "foreign_key": [
        {"column": "student_id", "reference": {"table": "student", "column": "student_id"}},
        {"column": "enrollment_id", "reference": {"table": "enrollment_fact", "column": "enrollment_id"}}
    ],
    "table_type": "fact",
}

SCORE = {
    "name": "score_fact",
    "schema": [
        {"name": "score_id", "type": "BIGINT", "primary_key": True},
        {"name": "instruction_id", "type": "BIGINT"},
        {"name": "student_id", "type": "STRING"},
        {"name": "final_score", "type": "DOUBLE"},
        {"name": "final_score_4", "type": "DOUBLE"},
        {"name": "academic_rank", "type": "STRING"},
        {"name": "is_practice", "type": "BOOLEAN"},
        {"name": "last_modified_date", "type": "TIMESTAMP"},
        {"name": "etl_date", "type": "TIMESTAMP"}
    ],
    "primary_key": ["score_id"],
    "foreign_key": [
        {"column": "instruction_id", "reference": {"table": "instruction_fact", "column": "instruction_id"}},
        {"column": "student_id", "reference": {"table": "student", "column": "student_id"}}
    ],
    "table_type": "fact",
}

SCORE_DETAIL = {
    "name": "score_detail",
    "schema": [
        {"name": "score_detail_id", "type": "BIGINT", "primary_key": True},
        {"name": "score_id", "type": "BIGINT"},
        {"name": "regular_score_1", "type": "DOUBLE"},
        {"name": "regular_score_2", "type": "DOUBLE"},
        {"name": "regular_score_3", "type": "DOUBLE"},
        {"name": "mid_term_score", "type": "DOUBLE"},
        {"name": "final_term_score", "type": "DOUBLE"},
        {"name": "practice_score_1", "type": "DOUBLE"},
        {"name": "practice_score_2", "type": "DOUBLE"},
        {"name": "practice_score_3", "type": "DOUBLE"},
        {"name": "last_modified_date", "type": "TIMESTAMP"}
    ],
    "primary_key": ["score_detail_id"],
    "foreign_key": [
        {"column": "score_id", "reference": {"table": "score_fact", "column": "score_id"}}
    ],
    "table_type": "fact",
}

ALL_TABLES = {
    EMPLOYEE["name"]: EMPLOYEE,
    LECTURER["name"]: LECTURER,
    PROGRAM["name"]: PROGRAM,
    PROGRAM_SEMESTER["name"]: PROGRAM_SEMESTER,
    COURSE["name"]: COURSE,
    CLASS["name"]: CLASS,
    ADDRESS["name"]: ADDRESS,
    STUDENT["name"]: STUDENT,
    INSTRUCTION["name"]: INSTRUCTION,
    INSTRUCTION_LECTURER["name"]: INSTRUCTION_LECTURER,
    ENROLLMENT["name"]: ENROLLMENT,
    ENROLL_STUDENT["name"]: ENROLL_STUDENT,
    SCORE["name"]: SCORE,
    SCORE_DETAIL["name"]: SCORE_DETAIL
}