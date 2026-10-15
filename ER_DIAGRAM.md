erDiagram
    ORGANIZATIONS {
        varchar(20) organization_id PK
        varchar(150) organization_name
        varchar(255) logo_path
        varchar(7) theme_primary_color
        varchar(7) theme_accent_color
    }

    ADMINISTRATORS {
        int admin_id PK
        varchar(20) organization_id FK
        varchar(150) full_name
        varchar(150) email
        varchar(255) password_hash
        timestamp date_added
    }

    GRADE_SCALES {
        varchar(20) scale_id PK
        varchar(150) label
        decimal(6_2) min_value
        decimal(6_2) max_value
        decimal(6_2) best_value
        decimal(6_2) passing_value
        tinyint(1) higher_is_better
        varchar(255) notes
    }

    SCHOLARSHIP_PROGRAMS {
        int scholarship_id PK
        varchar(20) organization_id FK
        varchar(150) scholarship_name
        varchar(150) provider
        varchar(20) grade_scale FK
        decimal(6_2) gwa_limit
        decimal(12_2) income_cap
        enum eligible_field
        varchar(20) eligible_years
        varchar(100) location_req
        int min_entrance
        int available_slots
        enum status
        date application_deadline
        timestamp date_added
    }

    APPLICANTS {
        int applicant_id PK
        int scholarship_id FK
        varchar(150) full_name
        decimal(6_2) gwa
        int entrance_score
        decimal(12_2) household_income
        varchar(100) course
        tinyint year_level
        varchar(100) location
        timestamp date_added
    }

    SCREENING_RESULTS {
        int result_id PK
        int applicant_id FK
        int scholarship_id FK
        boolean eligible
        timestamp date_screened
    }

    SCREENING_REASONS {
        int reason_id PK
        int result_id FK
        varchar(50) criterion_name
        varchar(50) applicant_value
        varchar(50) threshold_value
        boolean met
    }

    RANKING_RESULTS {
        int ranking_id PK
        int result_id FK
        decimal(5_2) priority_score
        int rank_position
        enum status
        timestamp date_ranked
    }

    ORGANIZATIONS ||--o{ ADMINISTRATORS : "manages"
    ORGANIZATIONS ||--o{ SCHOLARSHIP_PROGRAMS : "owns"
    GRADE_SCALES ||--o{ SCHOLARSHIP_PROGRAMS : "enforces"
    SCHOLARSHIP_PROGRAMS ||--o{ APPLICANTS : "receives"
    SCHOLARSHIP_PROGRAMS ||--o{ SCREENING_RESULTS : "yields"
    APPLICANTS ||--o{ SCREENING_RESULTS : "undergoes"
    SCREENING_RESULTS ||--o{ SCREENING_REASONS : "contains"
    SCREENING_RESULTS ||--o| RANKING_RESULTS : "progresses to"
