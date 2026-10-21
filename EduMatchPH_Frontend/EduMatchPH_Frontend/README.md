# EduMatch PH: Administrator Frontend

Plain HTML, CSS and JavaScript. No build step. Talks to backend v2.

## Pages
| File | What it does |
|---|---|
| index.html | Login (choose UCLM or DOST) |
| programs.html | List of your organization's programs |
| program-form.html | Create / edit a program (grade scale, GWA limit, rules, slots, status) |
| applicants.html | Add applicant, import .csv/.xlsx (preview then save), Run Screening, per-criterion reasons, delete applicant |
| ranking.html | Run Ranking, shortlist/waitlist table, "Why?" explanation, download CSV |
| compare.html | Compare two ranked applicants side by side |
| app.js | Shared code: apiFetch, login/logout, header, dropdowns |
| style.css | Team colors and styles |

## How to run
1. Start XAMPP MySQL. Load edumatch_schema_v5.sql in phpMyAdmin.
2. In the backend folder: `python app.py` (runs on http://localhost:5000).
3. In THIS folder: `python -m http.server 5500`, or VS Code Live Server on port 5500.
4. Open **http://localhost:5500/index.html**. Use `localhost`, not `127.0.0.1`, or the login cookie is not sent.

Demo logins (password `admin123`): alicia.ramos@uclm.edu.ph (UCLM), marco.villanueva@dost.gov.ph (DOST).

## If the backend uses a different address
Change `const API` at the top of app.js. The backend CORS list must include the page's address.

## Tested
26 browser checks (Playwright/Chromium, sandbox only) against backend v2: login, wrong password,
organization isolation, create/edit program, grade-scale hint, add/import/delete applicants,
screening, ranking, explanation, CSV export, compare, Closed disables Run Ranking.
Re-run on your own machine before the demo.
