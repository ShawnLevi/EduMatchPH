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

## What changed in the UI upgrade
- Program cards with search and status filters; workflow stepper (Add applicants → Screening → Ranking → Shortlist) on every program page.
- Applicants: one searchable, sortable, paginated table; expandable rows show the six checks; clickable stat tiles filter; "Add applicant" dialog with inline validation; drag-and-drop import with preview and a template download; "not screened yet" banner after new applicants are added.
- Ranking: score bars, a visible cut-off line at the number of slots, a "Why?" side drawer (score gauge, plain-language top drivers, green/red contribution bars, next/previous), tick two rows to compare.
- Compare: side-by-side cards with the leader highlighted and a mirrored contribution chart. The URL can be shared.
- Program form: live rule summary, unsaved-changes guard, Ctrl+S, confirmation before rule changes.
- Toasts instead of inline messages, styled confirm dialogs instead of confirm(), skeleton loading, button spinners, "/" focuses the search box, responsive layout, respects reduced-motion.

The new optional backend route `GET /api/scholarships/<id>/applicants` (in `app.py`) lets the table show applicants before screening. The frontend still works without it (it falls back to the screening data).
