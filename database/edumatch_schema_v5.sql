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
    audit_logs,
    applicant_requirements, program_requirements, requirement_types,
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
    theme_primary_color VARCHAR(7),            -- hex, e.g. '#0B1E3D'
    theme_accent_color VARCHAR(7),
    theme_bg_color VARCHAR(7),                 -- hex, e.g. '#FBF8F2' (center content block)
    theme_bg_image MEDIUMTEXT NULL,            -- optional background image URL / data URI
    theme_bg_opacity DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    theme_surface_opacity DECIMAL(3,2) NOT NULL DEFAULT 0.94
);

CREATE TABLE administrators (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    organization_id VARCHAR(20) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('owner', 'admin', 'super_admin') NOT NULL DEFAULT 'admin',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_login TIMESTAMP NULL,
    failed_attempts INT NOT NULL DEFAULT 0,
    must_change_pw TINYINT(1) NOT NULL DEFAULT 0,
    avatar_url MEDIUMTEXT NULL,
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
    eligible_field ENUM('ANY','STEM','BUSINESS','MARITIME','CRIMINOLOGY','NURSING','EDUCATION') NOT NULL DEFAULT 'ANY',
    eligible_years VARCHAR(20) NOT NULL,       -- comma list, e.g. '1,2,3,4,5' — parsed in application code
    location_req VARCHAR(100) NOT NULL DEFAULT 'Nationwide',
    min_entrance INT NOT NULL DEFAULT 0,
    available_slots INT,
    status ENUM('Open','Screening','Ranking','Closed') DEFAULT 'Open',
    is_archived TINYINT(1) NOT NULL DEFAULT 0,
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
    year_level TINYINT NOT NULL,               -- 1–5
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
    UNIQUE KEY uq_screening_applicant_program (applicant_id, scholarship_id),
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
    priority_score DECIMAL(5,2) NOT NULL,      -- 0–100, from the trained model
    rank_position INT,
    status ENUM('SHORTLIST','WAITLIST') NOT NULL,
    date_ranked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ranking_result (result_id),
    FOREIGN KEY (result_id) REFERENCES screening_results(result_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- CLUSTER 6: PROGRAM-SPECIFIC PREREQUISITES
-- ------------------------------------------------------------

CREATE TABLE requirement_types (
    requirement_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    label VARCHAR(120) NOT NULL,
    value_kind ENUM('YES_NO','NUMBER','DOCUMENT','CHOICE') NOT NULL,
    unit VARCHAR(20) NULL,
    is_sensitive TINYINT(1) NOT NULL DEFAULT 0,
    notes VARCHAR(255) NULL
);

CREATE TABLE program_requirements (
    program_req_id INT AUTO_INCREMENT PRIMARY KEY,
    scholarship_id INT NOT NULL,
    requirement_id INT NOT NULL,
    min_value DECIMAL(8,2) NULL,
    max_value DECIMAL(8,2) NULL,
    expected_choice VARCHAR(60) NULL,
    is_mandatory TINYINT(1) NOT NULL DEFAULT 1,
    UNIQUE KEY uq_program_requirement (scholarship_id, requirement_id),
    FOREIGN KEY (scholarship_id) REFERENCES scholarship_programs(scholarship_id) ON DELETE CASCADE,
    FOREIGN KEY (requirement_id) REFERENCES requirement_types(requirement_id)
);

CREATE TABLE applicant_requirements (
    applicant_req_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    requirement_id INT NOT NULL,
    value_number DECIMAL(8,2) NULL,
    value_text VARCHAR(60) NULL,
    status ENUM('NOT_SUBMITTED','SUBMITTED','VERIFIED','REJECTED') NOT NULL DEFAULT 'NOT_SUBMITTED',
    verified_on DATE NULL,
    UNIQUE KEY uq_applicant_requirement (applicant_id, requirement_id),
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id) ON DELETE CASCADE,
    FOREIGN KEY (requirement_id) REFERENCES requirement_types(requirement_id)
);

-- ------------------------------------------------------------
-- CLUSTER 7: AUDIT LOGS (read-only accountability trail)
-- ------------------------------------------------------------

CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    organization_id VARCHAR(20) NULL,
    admin_id INT NULL,
    action VARCHAR(60) NOT NULL,
    target_type VARCHAR(40) NULL,
    target_id VARCHAR(60) NULL,
    details VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE SET NULL,
    FOREIGN KEY (admin_id) REFERENCES administrators(admin_id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- STARTER DATA
-- ------------------------------------------------------------

INSERT INTO organizations (organization_id, organization_name, theme_primary_color, theme_accent_color, theme_bg_color) VALUES
('dost', 'Department of Science and Technology', '#003DA5', '#FDB813', '#F5F7FB'),
('uclm', 'University of Cebu Lapu-Lapu and Mandaue', '#0B1E3D', '#E8A63C', '#FBF8F2');
-- NOTE: colors are placeholders — verify against each organization's real brand guide before any demo.

-- All demo accounts use the password: admin123 (stored as a PBKDF2-SHA256 hash with a unique salt per account).
-- Make hashes for new accounts with hash_password.py.
INSERT INTO administrators (organization_id, full_name, email, password_hash, role, is_active, must_change_pw) VALUES
('uclm', 'Alicia Ramos', 'alicia.ramos@uclm.edu.ph', 'pbkdf2:sha256:1000000$XEeahqdWeTXXeckP$2a1ee5311e704f1ede888a5e2943141a5ad4542efee993338142412334c56402', 'admin', 1, 0),
('dost', 'Marco Villanueva', 'marco.villanueva@dost.gov.ph', 'pbkdf2:sha256:1000000$PU2AoDZVatgg2NAM$448cf6b6405c3d229e22b1f91fc9f1b604fb5b1d3f4fff37eaa8bd6321505e93', 'admin', 1, 0),
('uclm', 'System Super Admin', 'superadmin@edumatch.ph', 'pbkdf2:sha256:1000000$wjPLTHtyVtmX3sxx$39feaa3c6972e071d5db81a9d46406b48e7c55e4a345ff0c6b0436452a7d2721', 'super_admin', 1, 0);

INSERT INTO requirement_types (code, label, value_kind, unit, is_sensitive, notes) VALUES
('MEDICAL_CLEARANCE', 'PEME / Medical Clearance', 'YES_NO', NULL, 1, 'Store clearance result only, not medical details (RA 10173).'),
('MIN_HEIGHT_CM', 'Minimum Height', 'NUMBER', 'cm', 0, 'Used by Maritime and Criminology programs.'),
('DRUG_TEST', 'Drug Test Clearance', 'YES_NO', NULL, 1, 'Store clearance result only.'),
('POLICE_CLEARANCE', 'Police / NBI Clearance', 'DOCUMENT', NULL, 0, 'Required for Criminology.'),
('INDIGENCY_CERT', 'Certificate of Indigency / ITR', 'DOCUMENT', NULL, 0, 'Financial need verification.');

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
