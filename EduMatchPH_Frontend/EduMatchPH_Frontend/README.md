# EduMatch PH: Administrator Frontend

Plain HTML, CSS and JavaScript. No build step. Talks to backend v2.

## Pages
| File | What it does |
|---|---|
| index.html | Login (choose UCLM or DOST) |
| programs.html | List of your organization's programs |
| program-form.html | Create / edit a program (grade scale, GWA limit, rules, slots, status) |
| applicants.html | Add or edit an applicant, import .csv/.xlsx (preview then save, download problem rows), tick applicants to screen or delete them, Delete all, Undo, export applicants and screening reasons, "why not eligible" summary, Run Screening, per-criterion reasons |
| ranking.html | Run Ranking, shortlist/waitlist table, "Why?" explanation, Edit applicant, download CSV, print the shortlist |
| compare.html | Compare two ranked applicants side by side |
| app.js | Shared code: apiFetch, login/logout, header, dropdowns |
| style.css | Team colors and styles |

## How to run
1. Start XAMPP MySQL. Load edumatch_schema_v5.sql in phpMyAdmin.
2. In the backend folder: `python app.py` (runs on http://localhost:5000).
3. In THIS folder: `python -m http.server 5500`, or VS Code Live Server on port 5500.
4. Open **http://localhost:5500/index.html**. Use `localhost`, not `127.0.0.1`, or the login cookie is not sent.

Administrator accounts are provisioned by the project team for each organization.

## If the backend uses a different address
Change `const API` at the top of app.js. The backend CORS list must include the page's address.

## Editing applicants after screening or ranking
The pencil icon on an applicant row (or the Edit button on the ranking page) opens the same form with the saved details. After saving, if the applicant had already been screened, the system asks whether to screen that applicant only, or screen everyone again. If the program had already been ranked, the choice is to screen and rank that applicant only, or screen and rank everyone again. Choosing "Decide later" leaves the applicant marked Not screened.

## Selecting, deleting and exporting applicants
- Tick applicants (or the box in the table header for the whole page, then "Select all N matching" to include every applicant that matches the current filter). A bar appears with **Screen selected**, **Delete selected** and **Clear selection**.
- **Delete all** asks you to type the program name. Every delete (one, selected or all) shows an **Undo** button for about 8 seconds; restored applicants come back as Not screened.
- **Export applicants** and **Export reasons** download CSV files (applicant list with screening and ranking results; the six criteria for each screened applicant).
- After screening, **Why applicants were not eligible** shows how many applicants failed each rule and how many missed by one rule only.
- Import: when rows have problems, **Download problem rows (CSV)** gives a file with the original values, ready to fix and upload again.
- Ranking page: **Print shortlist** prints a clean page with the program name, slots and date.

## What changed in the UI upgrade
- Program cards with search and status filters; workflow stepper (Add applicants → Screening → Ranking → Shortlist) on every program page.
- Applicants: one searchable, sortable, paginated table; expandable rows show the six checks; clickable stat tiles filter; "Add applicant" dialog with inline validation; drag-and-drop import with preview and a template download; "not screened yet" banner after new applicants are added.
- Ranking: score bars, a visible cut-off line at the number of slots, a "Why?" side drawer (score gauge, plain-language top drivers, green/red contribution bars, next/previous), tick two rows to compare.
- Compare: side-by-side cards with the leader highlighted and a mirrored contribution chart. The URL can be shared.
- Program form: live rule summary, unsaved-changes guard, Ctrl+S, confirmation before rule changes.
- Toasts instead of inline messages, styled confirm dialogs instead of confirm(), skeleton loading, button spinners, "/" focuses the search box, responsive layout, respects reduced-motion.

The new optional backend route `GET /api/scholarships/<id>/applicants` (in `app.py`) lets the table show applicants before screening. The frontend still works without it (it falls back to the screening data).
