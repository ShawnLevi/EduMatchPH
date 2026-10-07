-- ============================================================
-- EduMatch PH — Database Schema v5 (a grade scale per program)
-- Matches the actual trained model (edumatch_priority_model.joblib):
--   features = gwa, entrance_score, household_income,
--              sch_max_gwa, sch_min_entrance, sch_income_cap
-- GRADE SCALES: each scholarship program names the grade scale it asks for
-- (programs.grade_scale -> grade_scales). Examples: the senior high school
-- general average (0-100, higher is better) for incoming freshmen, or the
-- college GWA (1.00 best to 5.00, lower is better) for continuing students.
-- An applicant's GWA is stored AS ENTERED, in the program's scale.
-- The model reads a 0-100 'standing' worked out from the scale (backend code).
--   features = gwa (standing), entrance_score, household_income,
--              sch_min_gwa (standing of the program's limit), sch_min_entrance, sch_income_cap
-- No age, no academic track — both removed; year_level added instead.
-- Run this in phpMyAdmin's SQL tab, inside a fresh database
-- (e.g. edumatch_db).
-- ============================================================

DROP TABLE IF EXISTS
    ranking_results, screening_reasons, screening_results,
    applicants, scholarship_programs, grade_scales,
    administrators, organizations;

-- ------------------------------------------------------------
-- CLUSTER 1: TENANTS
-- ------------------------------------------------------------

CREATE TABLE organizations (
    organization_id VARCHAR(20) PRIMARY KEY,   -- e.g. 'dost', 'uclm'
    organization_name VARCHAR(150) NOT NULL,
    logo_path VARCHAR(255),
    theme_primary_color VARCHAR(7),            -- hex, e.g. '#002855'
    theme_accent_color VARCHAR(7)
);

CREATE TABLE administrators (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    organization_id VARCHAR(20) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- GRADE SCALES (shared by all organizations; add a row for a new scale)
-- ------------------------------------------------------------

CREATE TABLE grade_scales (
    scale_id VARCHAR(20) PRIMARY KEY,
    label VARCHAR(150) NOT NULL,
    min_value DECIMAL(6,2) NOT NULL,           -- lowest value that can be entered
    max_value DECIMAL(6,2) NOT NULL,           -- highest value that can be entered
    best_value DECIMAL(6,2) NOT NULL,          -- the best possible grade
    passing_value DECIMAL(6,2) NOT NULL,       -- the lowest passing grade
    higher_is_better TINYINT(1) NOT NULL,      -- 1 = higher is better, 0 = lower is better
    notes VARCHAR(255)
);

INSERT INTO grade_scales (scale_id, label, min_value, max_value, best_value, passing_value, higher_is_better, notes) VALUES
('SHS_PERCENT', 'Senior high school general average (0 to 100, higher is better)', 0, 100, 100, 75, 1, 'For incoming freshmen. Passing 75 per DepEd; confirm with the school.'),
('COLLEGE_1_5', 'College GWA (1.00 is best, 5.00 is worst, lower is better)', 1, 5, 1, 3, 0, 'UCLM college scale. Passing 3.00; confirm with the UCLM scholarship office.'),
('SCALE_5_BEST', 'Reversed scale (5.00 is best, 1.00 is worst, higher is better)', 1, 5, 5, 3, 1, 'EXAMPLE of a school that grades the opposite way. Confirm before real use.');

-- ------------------------------------------------------------
-- CLUSTER 2: SCHOLARSHIP PROGRAMS (corrected — 6 real criteria)
-- ------------------------------------------------------------

CREATE TABLE scholarship_programs (
    scholarship_id INT AUTO_INCREMENT PRIMARY KEY,
    organization_id VARCHAR(20) NOT NULL,
    scholarship_name VARCHAR(150) NOT NULL,
    provider VARCHAR(150),
    grade_scale VARCHAR(20) NOT NULL,          -- which scale this program asks for (grade_scales)
    gwa_limit DECIMAL(6,2) NOT NULL,           -- the WORST GWA still accepted, in that scale
    income_cap DECIMAL(12,2) NOT NULL,
    eligible_field ENUM('ANY','STEM','BUSINESS') NOT NULL DEFAULT 'ANY',
    eligible_years VARCHAR(20) NOT NULL,       -- comma list, e.g. '1,2,3,4' — parsed in application code
    location_req VARCHAR(100) NOT NULL DEFAULT 'Nationwide',
    min_entrance INT NOT NULL DEFAULT 0,
    available_slots INT,
    status ENUM('Open','Screening','Ranking','Closed') DEFAULT 'Open',
    application_deadline DATE,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
    FOREIGN KEY (grade_scale) REFERENCES grade_scales(scale_id)
);

-- ------------------------------------------------------------
-- CLUSTER 3: APPLICANTS (corrected — matches the trained model)
-- Applicants are scoped through their scholarship, not given
-- their own organization_id — avoids two sources of truth.
-- ------------------------------------------------------------

CREATE TABLE applicants (
    applicant_id INT AUTO_INCREMENT PRIMARY KEY,
    scholarship_id INT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    gwa DECIMAL(6,2) NOT NULL,                 -- as entered, in the PROGRAM'S grade scale
    entrance_score INT NOT NULL,               -- 0–100 (model trained on ~40–99)
    household_income DECIMAL(12,2) NOT NULL,   -- annual PHP (model trained on ~45,000–800,000)
    course VARCHAR(100) NOT NULL,
    year_level TINYINT NOT NULL,               -- 1–4
    location VARCHAR(100) NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scholarship_id) REFERENCES scholarship_programs(scholarship_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- CLUSTER 4: SCREENING (Stage 1 — rule-based, no ML)
-- ------------------------------------------------------------

CREATE TABLE screening_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    scholarship_id INT NOT NULL,
    eligible BOOLEAN NOT NULL,
    date_screened TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id) ON DELETE CASCADE,
    FOREIGN KEY (scholarship_id) REFERENCES scholarship_programs(scholarship_id) ON DELETE CASCADE
);

CREATE TABLE screening_reasons (
    reason_id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT NOT NULL,
    criterion_name VARCHAR(50) NOT NULL,       -- 'GWA', 'Income', 'Field', 'Year Level', 'Location', 'Entrance Score'
    applicant_value VARCHAR(50),
    threshold_value VARCHAR(50),
    met BOOLEAN NOT NULL,
    FOREIGN KEY (result_id) REFERENCES screening_results(result_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- CLUSTER 5: RANKING (Stage 2 — ML, eligible applicants only)
-- ------------------------------------------------------------

CREATE TABLE ranking_results (
    ranking_id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT NOT NULL,                    -- FK to the ELIGIBLE screening_result being ranked
    priority_score DECIMAL(5,2) NOT NULL,       -- 0–100, from the trained model
    rank_position INT,
    status ENUM('SHORTLIST','WAITLIST') NOT NULL,
    date_ranked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES screening_results(result_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- STARTER DATA
-- ------------------------------------------------------------

INSERT INTO organizations (organization_id, organization_name, theme_primary_color, theme_accent_color) VALUES
('dost', 'Department of Science and Technology', '#003DA5', '#FDB813'),
('uclm', 'University of Cebu Lapu-Lapu and Mandaue', '#002855', '#C8102E');
-- NOTE: colors are placeholders — verify against each organization's real brand guide before any demo.

-- Both demo accounts use the password: admin123 (stored as a hash).
-- Make hashes for new accounts with hash_password.py.
INSERT INTO administrators (organization_id, full_name, email, password_hash) VALUES
('uclm', 'Alicia Ramos', 'alicia.ramos@uclm.edu.ph', 'pbkdf2:sha256:1000000$qx7GyKcF15FYgxsm$700660967a9532a95050ae6b4826b0cee0703a43b763d859fee0811eee3f18f5'),
('dost', 'Marco Villanueva', 'marco.villanueva@dost.gov.ph', 'pbkdf2:sha256:1000000$qx7GyKcF15FYgxsm$700660967a9532a95050ae6b4826b0cee0703a43b763d859fee0811eee3f18f5');

INSERT INTO scholarship_programs
(organization_id, scholarship_name, provider, grade_scale, gwa_limit, income_cap, eligible_field, eligible_years, location_req, min_entrance, available_slots, status) VALUES
('uclm', 'Academic Excellence Scholarship', 'University of Cebu LM', 'COLLEGE_1_5',  1.80, 500000, 'ANY',      '1,2,3,4', 'Nationwide', 85, 20, 'Open'),
('uclm', 'Presidential Scholarship',        'University of Cebu LM', 'SHS_PERCENT', 95.00, 900000, 'ANY',      '1',       'Nationwide', 90, 5,  'Open'),
('uclm', 'Financial Assistance Grant',      'University of Cebu LM', 'COLLEGE_1_5',  2.60, 180000, 'ANY',      '1,2,3,4', 'Cebu',       60, 30, 'Open'),
('dost', 'S&T Undergraduate Scholarship',   'DOST-SEI',              'SHS_PERCENT', 88.00, 400000, 'STEM',     '1',       'Nationwide', 80, 15, 'Open'),
('dost', 'RA 7687 Merit Grant',             'DOST-SEI',              'COLLEGE_1_5',  2.20, 300000, 'STEM',     '1,2,3,4', 'Nationwide', 78, 10, 'Open');

-- A few sample applicants. Each GWA is in the scale of the program it applies to
-- (programs 1 and 3: college 1.00-5.00; programs 2 and 4: senior high school 0-100).
INSERT INTO applicants (scholarship_id, full_name, gwa, entrance_score, household_income, course, year_level, location) VALUES
(1, 'Juan Dela Cruz',  1.48, 88, 180000, 'BS Computer Science', 3, 'Lapu-Lapu City'),
(1, 'Maria Santos',    1.68, 82, 220000, 'BS Information Technology', 2, 'Cebu City'),
(3, 'Pedro Reyes',     2.44, 65, 150000, 'BS Business Administration', 2, 'Mandaue City'),
(4, 'Ana Villareal',   90.00, 85, 250000, 'BS Computer Science', 1, 'Cebu City'),
(4, 'Mark Tan',        89.50, 81, 310000, 'BS Civil Engineering', 1, 'Talisay City');
