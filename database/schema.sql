-- EduMatch PH — Database Schema
--
-- Multi-tenant scoping: every administrator and scholarship_program belongs to
-- exactly one organization. Applicants are scoped INDIRECTLY through the
-- scholarship_program they applied to — do not add organization_id directly to
-- applicants (or any table below it), since that would create two sources of
-- truth that could drift out of sync. See the reminder at the bottom of this
-- file for how this must be enforced once Flask routes exist.

CREATE TABLE organizations (
    organization_id VARCHAR(20) PRIMARY KEY,   -- e.g. 'dost', 'uclm'
    organization_name VARCHAR(150) NOT NULL,
    logo_path VARCHAR(255),
    theme_primary_color VARCHAR(7),   -- hex, e.g. '#003DA5'
    theme_accent_color VARCHAR(7)
);

CREATE TABLE administrators (
    administrator_id INT AUTO_INCREMENT PRIMARY KEY,
    organization_id VARCHAR(20) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Scholarship Administrator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE TABLE scholarship_programs (
    scholarship_id INT AUTO_INCREMENT PRIMARY KEY,
    organization_id VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    provider VARCHAR(200) NOT NULL,
    description TEXT,
    minimum_gpa DECIMAL(4,2),
    income_cap DECIMAL(12,2),
    eligible_field VARCHAR(200),
    location_requirement VARCHAR(200),
    minimum_entrance_score DECIMAL(6,2),
    deadline DATE,
    available_slots INT,
    status VARCHAR(20) NOT NULL DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

-- Applicants are scoped ONLY through scholarship_id -> scholarship_programs.organization_id.
-- Do NOT add an organization_id column here.
CREATE TABLE applicants (
    applicant_id INT AUTO_INCREMENT PRIMARY KEY,
    scholarship_id INT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    course VARCHAR(150),
    year_level VARCHAR(20),
    gpa DECIMAL(5,2),
    household_income DECIMAL(12,2),
    location VARCHAR(150),
    citizenship VARCHAR(100),
    entrance_test_score DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scholarship_id) REFERENCES scholarship_programs(scholarship_id)
);

-- Stage 1 — rule-based eligibility screening result, one row per applicant per scholarship.
CREATE TABLE screening_results (
    screening_result_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    scholarship_id INT NOT NULL,
    is_eligible BOOLEAN NOT NULL,
    screened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id),
    FOREIGN KEY (scholarship_id) REFERENCES scholarship_programs(scholarship_id)
);

-- Criterion-level pass/fail detail behind each screening_results row — the audit trail.
CREATE TABLE screening_reasons (
    screening_reason_id INT AUTO_INCREMENT PRIMARY KEY,
    screening_result_id INT NOT NULL,
    criterion_name VARCHAR(100) NOT NULL,
    passed BOOLEAN NOT NULL,
    FOREIGN KEY (screening_result_id) REFERENCES screening_results(screening_result_id)
);

-- Stage 2 — ML priority ranking, only for applicants who already passed screening.
CREATE TABLE ranking_results (
    ranking_result_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    scholarship_id INT NOT NULL,
    priority_score DECIMAL(6,2) NOT NULL,
    rank_position INT NOT NULL,
    ranked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id),
    FOREIGN KEY (scholarship_id) REFERENCES scholarship_programs(scholarship_id)
);

INSERT INTO organizations (organization_id, organization_name) VALUES
('dost', 'Department of Science and Technology'),
('uclm', 'University of Cebu Lapu-Lapu and Mandaue');

-- ============================================================================
-- REMINDER FOR WHOEVER BUILDS THE FLASK ROUTES:
-- Every SELECT that touches scholarship_programs, applicants (via JOIN through
-- scholarship_programs), screening_results, screening_reasons, or ranking_results
-- MUST include a `WHERE scholarship_programs.organization_id = ?` clause (or an
-- equivalent JOIN condition), using the logged-in administrator's organization_id
-- from their server-side session — never from a client-supplied value (query
-- param, form field, header). This is not implemented yet since there is no
-- backend; do not forget it when the Flask routes are added.
-- ============================================================================
