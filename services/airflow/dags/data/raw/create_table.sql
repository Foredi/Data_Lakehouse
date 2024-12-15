CREATE TABLE employee (
    employee_id SERIAL PRIMARY KEY,
    employee_name TEXT,
    date_of_birth TIMESTAMP,
    nationality TEXT,
    national_id TEXT,
    insurance_id TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lecturer (
    lecturer_id SERIAL PRIMARY KEY UNIQUE,
    employee_id BIGINT,
    academic_title VARCHAR(20),
    academic_title_date TIMESTAMP,
    degree VARCHAR(50),
    degree_issue_date TIMESTAMP,
    degree_issue_place VARCHAR(100),
    major VARCHAR(100),
    department VARCHAR(100),
    number_of_exp BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee (employee_id)
);

CREATE TABLE program (
    program_id VARCHAR(10) PRIMARY KEY UNIQUE,
    class_of VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE program_semester (
    program_semester_id VARCHAR(10) PRIMARY KEY UNIQUE,
    program_id VARCHAR(10),
    semester_name VARCHAR(20),
    total_credit BIGINT,
    required_credit BIGINT,
    elective_credit BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES program (program_id)
);

CREATE TABLE course (
    course_id BIGINT PRIMARY KEY UNIQUE,
    course_name VARCHAR(200),
    course_code BIGINT,
    category VARCHAR(100),
    total_credit BIGINT,
    theory_credit BIGINT,
    practice_credit BIGINT,
    self_learning_credit BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE program_course (
    program_semester_id VARCHAR(10),
    course_id BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (program_semester_id, course_id),
    FOREIGN KEY (program_semester_id) REFERENCES program_semester(program_semester_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
);

CREATE TABLE class (
    class_id BIGINT PRIMARY KEY UNIQUE,
    class_name VARCHAR(100),
    class_type VARCHAR(20),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE instruction_fact (
    instruction_id SERIAL PRIMARY KEY UNIQUE,
    program_semester_id VARCHAR(10),
    course_id BIGINT,
    class_id BIGINT,
    is_required BOOL,
    num_student BIGINT,
    num_pass_student BIGINT,
    num_fail_student BIGINT,
    avg_final_score FLOAT,
    instruction_status VARCHAR(100),
    instruction_allocate TIMESTAMP,
    instruction_time_start TIMESTAMP,
    instruction_time_end TIMESTAMP,
    last_modified_date TIMESTAMP,
    etl_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_semester_id) REFERENCES program_semester (program_semester_id),
    FOREIGN KEY (course_id) REFERENCES course (course_id),
    FOREIGN KEY (class_id) REFERENCES class (class_id)
);

CREATE TABLE instruction_lecturer (
    instruction_lecturer_id BIGINT PRIMARY KEY UNIQUE,
    instruction_id BIGINT,
    lecturer_id BIGINT,
    lecturer_type VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instruction_id) REFERENCES instruction_fact (instruction_id),
    FOREIGN KEY (lecturer_id) REFERENCES lecturer (lecturer_id)
);

CREATE TABLE address (
    address_id SERIAL PRIMARY KEY UNIQUE,
    ward VARCHAR(100),
    district VARCHAR(100),
    city VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student (
    student_id VARCHAR(20) PRIMARY KEY UNIQUE,
    student_name VARCHAR(100),
    class_name VARCHAR(100),
    edu_mail VARCHAR(100),
    address_id BIGINT,
    national_id BIGINT,
    key_year VARCHAR(100),
    gender VARCHAR(3),
    student_dob TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (address_id) REFERENCES address (address_id)
);

CREATE TABLE enrollment_fact (
    enrollment_id SERIAL PRIMARY KEY UNIQUE,
    instruction_id BIGINT,
    enrollment_start_time TIMESTAMP,
    enrollment_end_time TIMESTAMP,
    enrollment_status VARCHAR(100),
    last_modified_date TIMESTAMP,
    etl_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instruction_id) REFERENCES instruction_fact (instruction_id)
);

CREATE TABLE enroll_student (
    student_id VARCHAR(20),
    enrollment_id BIGINT,
    enrollment_time TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, enrollment_id),
    FOREIGN KEY (student_id) REFERENCES student (student_id),
    FOREIGN KEY (enrollment_id) REFERENCES enrollment_fact (enrollment_id)
);

CREATE TABLE score_fact (
    score_id SERIAL PRIMARY KEY UNIQUE,
    instruction_id BIGINT,
    student_id VARCHAR(20),
    final_score FLOAT,
    final_score_4 FLOAT,
    academic_rank VARCHAR(100),
    is_practice BOOL,
    last_modified_date TIMESTAMP,
    etl_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instruction_id) REFERENCES instruction_fact (instruction_id),
    FOREIGN KEY (student_id) REFERENCES student (student_id)
);

CREATE TABLE score_detail (
    score_detail_id SERIAL PRIMARY KEY UNIQUE,
    score_id BIGINT,
    regular_score_1 FLOAT,
    regular_score_2 FLOAT,
    regular_score_3 FLOAT,
    mid_term_score FLOAT,
    final_term_score FLOAT,
    practice_score_1 FLOAT,
    practice_score_2 FLOAT,
    practice_score_3 FLOAT,
    last_modified_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (score_id) REFERENCES score_fact (score_id)
);