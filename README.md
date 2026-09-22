# 🎓 EduMatch PH — Scholarship Screening & Ranking System

A multi-tenant, web-based decision-support system that helps scholarship administrators automate the screening and prioritization of applicants against published eligibility criteria.

EduMatch PH is **not** a student-facing scholarship finder. It is used by **scholarship administrators** — university scholarship offices, government agencies, and private foundations — to process applicant pools for the scholarship programs they manage.

## What it does

1. An administrator, belonging to a specific registered **organization**, logs in and manages that organization's scholarship programs and applicant records.
2. **Eligibility Screening (rule-based, no ML):** each applicant is checked deterministically against a scholarship's published criteria (minimum GPA, income ceiling, eligible course/field, location requirement, minimum entrance score). Every result records which specific criteria were met or failed.
3. **Priority Ranking (machine learning):** applicants who pass eligibility screening are ranked using a trained model, so administrators can prioritize fairly when qualified applicants outnumber available slots.
4. The administrator reviews an explainable, ranked shortlist and makes the final award decision. **The system never awards a scholarship automatically** — it is decision support, not an automated award mechanism.

Every organization's scholarships, applicants, and results are kept fully separate from every other organization's data.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (no framework) |
| Backend | Python + Flask |
| Machine Learning | Python + scikit-learn |
| Database | MySQL (via XAMPP / phpMyAdmin) |

## Repository structure

```
EduMatchPH/
├── frontend/         # HTML/CSS/JS admin interface
├── backend/          # Flask API (auth, scholarships, applicants, screening, ranking)
├── database/         # MySQL schema and seed data
├── model/            # ML training scripts, synthetic dataset, saved model artifacts
└── README.md
```

> **Current status:** the frontend exists as a static prototype using mock/seed data (no backend, database, or model are connected yet). See open issues below.

## Core entities

- **Organization** — a university, agency, or foundation using the platform
- **Administrator** — a user account belonging to exactly one organization
- **Scholarship Program** — a scholarship record with published eligibility criteria, owned by one organization
- **Applicant** — a student record submitted for screening against one or more scholarship programs
- **Screening Result** — the eligibility outcome (eligible/ineligible) for one applicant against one scholarship, with a criterion-level breakdown
- **Ranking** — the priority score and rank position assigned to eligible applicants
- **Shortlist** — the subset of eligible, ranked applicants forwarded for administrator review

## Data note

The machine learning component is trained on a **synthetic dataset** generated for this project. Real, individual-level records connecting applicants to actual scholarship award outcomes are not publicly available, since such data is private and confidential. This is disclosed intentionally — the system demonstrates that the screening-and-ranking pipeline works correctly, not an empirical finding about real-world scholarship awarding.

## Git workflow

### Branch naming

Use `type/short-description`, for example:

- `feature/organization-scoping`
- `feature/eligibility-screening`
- `feature/priority-ranking`
- `feature/scholarship-management`
- `fix/applicant-upload-validation`
- `docs/readme-update`

### Commit messages

Write commits in the imperative mood, describing what the change does:

- `Add organization table and scoping to admin queries`
- `Implement rule-based eligibility screening endpoint`
- `Add priority ranking model comparison script`
- `Fix shortlist removal button`
- `Update README to reflect screening and ranking system`

## Team

| Name | Role |
|---|---|
| Godinez, Shawn Levi V. |Project Manager / Systems Analyst |
| Tan, Vinz Hyster | Backend / Database Developer |
| Monte, Jhaztene |Data Scientist / ML Lead  |
| Presbitero, Jhondel | Frontend / UI-UX Developer  |

**Adviser:** Virginia Verdun

## Academic context

Developed as a capstone project for the Methods of Research in Computing (ResCom), Software Engineering, and Data Science subjects, BSCS 3A, College of Computer Studies, University of Cebu Lapu-Lapu and Mandaue.