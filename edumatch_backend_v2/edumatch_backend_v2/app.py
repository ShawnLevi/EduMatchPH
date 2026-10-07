import csv
import io
import os

import openpyxl
from flask import Flask, Response, abort, jsonify, request, session
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash

from db import db, json_safe
from eligibility import check_eligibility
from ranking import explain_priority, predict_priority, program_standing
from reference import (COURSES, FIELDS, LOCALITIES, LOCATION_REQ_CHOICES,
                       STATUSES)
from validation import clean_applicant, clean_program

app = Flask(__name__)
# Change this secret before any real use. It signs the login cookie.
app.secret_key = os.environ.get("EDUMATCH_SECRET", "dev-only-change-me")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# The frontend runs on another port (for example 5500) on localhost, so allow
# localhost / 127.0.0.1 on any port, WITH cookies (the login).
CORS(app, supports_credentials=True,
     origins=r"http://(localhost|127\.0\.0\.1)(:\d+)?")


# ==================== VINZ: errors, login, access rules ====================

@app.errorhandler(HTTPException)
def http_error(e):
    return jsonify({"error": e.description}), e.code


@app.errorhandler(Exception)
def server_error(e):
    app.logger.exception("Unexpected error")
    return jsonify({"error": "Something went wrong on the server. "
                             "Check the backend terminal for details."}), 500


PUBLIC_ENDPOINTS = {"login", "logout", "me", "meta"}


@app.before_request
def require_login():
    if request.method == "OPTIONS" or request.endpoint in (None, "static"):
        return None
    if request.endpoint in PUBLIC_ENDPOINTS:
        return None
    if "admin_id" not in session:
        return jsonify({"error": "Please log in first"}), 401
    return None


def current_org():
    return session["organization_id"]


def load_scholarship(cur, scholarship_id):
    """The program, but only if it belongs to the logged-in organization.
    Another organization's id looks exactly like a missing one (404)."""
    cur.execute(
        "SELECT sp.*, gs.label AS grade_scale_label,"
        " gs.min_value AS scale_min, gs.max_value AS scale_max,"
        " gs.best_value AS scale_best, gs.passing_value AS scale_passing,"
        " gs.higher_is_better AS higher_is_better"
        " FROM scholarship_programs sp"
        " JOIN grade_scales gs ON gs.scale_id = sp.grade_scale"
        " WHERE sp.scholarship_id=%s AND sp.organization_id=%s",
        (scholarship_id, current_org()),
    )
    row = cur.fetchone()
    if row is None:
        abort(404, "Scholarship not found")
    return row


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "Send a JSON body")
    return data


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    org = str(data.get("organization_id") or "").strip()
    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "")
    if not (org and email and password):
        abort(400, "organization_id, email, and password are required")
    with db() as (conn, cur):
        cur.execute(
            "SELECT * FROM administrators"
            " WHERE email=%s AND organization_id=%s", (email, org))
        admin = cur.fetchone()
    if admin is None or not check_password_hash(admin["password_hash"], password):
        abort(401, "Wrong email or password for this organization")
    session.clear()
    session["admin_id"] = admin["admin_id"]
    session["organization_id"] = admin["organization_id"]
    session["full_name"] = admin["full_name"]
    return jsonify({"admin_id": admin["admin_id"],
                    "full_name": admin["full_name"],
                    "organization_id": admin["organization_id"]})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me", methods=["GET"])
def me():
    if "admin_id" not in session:
        abort(401, "Not logged in")
    return jsonify({"admin_id": session["admin_id"],
                    "full_name": session["full_name"],
                    "organization_id": session["organization_id"]})


@app.route("/api/meta", methods=["GET"])
def meta():
    """Lists for the form dropdowns, so the frontend never hardcodes them."""
    return jsonify({"courses": COURSES, "localities": LOCALITIES,
                    "location_req_choices": LOCATION_REQ_CHOICES,
                    "fields": FIELDS, "statuses": STATUSES,
                    "grade_scales": load_scales()})


# ==================== VINZ: applicant + screening routes ====================

def load_scales(cur=None):
    """All grade scales, as a list (for /api/meta) or a dict by id."""
    with db() as (conn, c):
        c.execute("SELECT scale_id, label, min_value, max_value, best_value,"
                  " passing_value, higher_is_better, notes FROM grade_scales"
                  " ORDER BY scale_id")
        rows = [json_safe(r) for r in c.fetchall()]
    for r in rows:
        r["higher_is_better"] = bool(r["higher_is_better"])
    return rows


def scales_by_id():
    return {r["scale_id"]: r for r in load_scales()}


def program_scale(program):
    return {"min_value": program["scale_min"], "max_value": program["scale_max"]}


def program_json(row):
    out = json_safe({k: row[k] for k in SCHOLARSHIP_COLS})
    out["grade_scale_label"] = row["grade_scale_label"]
    out["higher_is_better"] = bool(row["higher_is_better"])
    return out


def applicant_exists(cur, scholarship_id, a):
    cur.execute(
        "SELECT 1 FROM applicants WHERE scholarship_id=%s"
        " AND LOWER(full_name)=LOWER(%s) AND course=%s AND year_level=%s"
        " AND location=%s LIMIT 1",
        (scholarship_id, a["full_name"], a["course"], a["year_level"],
         a["location"]))
    return cur.fetchone() is not None


INSERT_APPLICANT = (
    "INSERT INTO applicants (scholarship_id, full_name, gwa, entrance_score,"
    " household_income, course, year_level, location)"
    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")


def applicant_values(scholarship_id, a):
    return (scholarship_id, a["full_name"], a["gwa"], a["entrance_score"],
            a["household_income"], a["course"], a["year_level"], a["location"])


@app.route("/api/scholarships/<int:scholarship_id>/applicants",
           methods=["POST"])
def add_applicant(scholarship_id):
    data = json_body()
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        clean, error = clean_applicant(data, program_scale(program))
        if error:
            abort(400, error)
        if applicant_exists(cur, scholarship_id, clean):
            abort(409, "This applicant is already in this program")
        cur.execute(INSERT_APPLICANT, applicant_values(scholarship_id, clean))
        conn.commit()
        return jsonify({"applicant_id": cur.lastrowid}), 201


@app.route("/api/scholarships/<int:scholarship_id>/screen", methods=["POST"])
def screen_scholarship(scholarship_id):
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        if scholarship["status"] == "Closed":
            abort(400, "This program is closed. Reopen it to run screening")

        # Clear the previous screening first, so pressing "Run Screening"
        # twice never creates duplicates. ON DELETE CASCADE also removes the
        # old reasons AND the old ranking: run ranking again after screening.
        cur.execute("DELETE FROM screening_results WHERE scholarship_id=%s",
                    (scholarship_id,))
        cur.execute("SELECT * FROM applicants WHERE scholarship_id=%s",
                    (scholarship_id,))
        results = []
        for a in cur.fetchall():
            is_eligible, checks = check_eligibility(a, scholarship)
            cur.execute(
                "INSERT INTO screening_results"
                " (applicant_id, scholarship_id, eligible) VALUES (%s,%s,%s)",
                (a["applicant_id"], scholarship_id, is_eligible))
            result_id = cur.lastrowid
            for name, (met, aval, tval) in checks.items():
                cur.execute(
                    "INSERT INTO screening_reasons (result_id, criterion_name,"
                    " applicant_value, threshold_value, met)"
                    " VALUES (%s,%s,%s,%s,%s)",
                    (result_id, name, str(aval), str(tval), met))
            results.append({"applicant_id": a["applicant_id"],
                            "eligible": bool(is_eligible)})
        cur.execute("UPDATE scholarship_programs SET status='Screening'"
                    " WHERE scholarship_id=%s", (scholarship_id,))
        conn.commit()
        return jsonify(results)


# ==================== VINZ: scholarship routes (Phase 2) ====================

SCHOLARSHIP_COLS = ["scholarship_id", "organization_id", "scholarship_name",
                    "provider", "grade_scale", "gwa_limit", "income_cap",
                    "eligible_field",
                    "eligible_years", "location_req", "min_entrance",
                    "available_slots", "status", "application_deadline"]
SCHOLARSHIP_COLUMNS = ", ".join(SCHOLARSHIP_COLS)

PROGRAM_FIELDS = ["scholarship_name", "provider", "grade_scale", "gwa_limit",
                  "income_cap",
                  "eligible_field", "eligible_years", "location_req",
                  "min_entrance", "available_slots", "status",
                  "application_deadline"]
CRITERIA_FIELDS = ["grade_scale", "gwa_limit", "income_cap", "eligible_field", "eligible_years",
                   "location_req", "min_entrance"]


def same_value(field, new, old):
    if field in ("gwa_limit", "income_cap"):  # Decimal vs float
        return float(new) == float(old)
    return str(new) == str(old)


@app.route("/api/scholarships", methods=["GET"])
def list_scholarships():
    # The organization comes from the login. The old ?organization_id= is
    # still accepted, but it must match the logged-in organization.
    org = request.args.get("organization_id") or current_org()
    if org != current_org():
        abort(403, "You can only view your own organization")
    with db() as (conn, cur):
        cur.execute(
            "SELECT sp.*, gs.label AS grade_scale_label,"
            " gs.higher_is_better AS higher_is_better"
            " FROM scholarship_programs sp JOIN grade_scales gs"
            " ON gs.scale_id = sp.grade_scale"
            " WHERE sp.organization_id=%s ORDER BY sp.scholarship_id", (org,))
        return jsonify([program_json(r) for r in cur.fetchall()])


@app.route("/api/scholarships/<int:scholarship_id>", methods=["GET"])
def get_scholarship(scholarship_id):
    with db() as (conn, cur):
        row = load_scholarship(cur, scholarship_id)
        return jsonify(program_json(row))


@app.route("/api/scholarships", methods=["POST"])
def create_scholarship():
    clean, error = clean_program(json_body(), scales_by_id())
    if error:
        abort(400, error)
    with db() as (conn, cur):
        cur.execute(
            "INSERT INTO scholarship_programs (organization_id, "
            + ", ".join(PROGRAM_FIELDS) + ") VALUES (%s,"
            + ",".join(["%s"] * len(PROGRAM_FIELDS)) + ")",
            (current_org(), *[clean[f] for f in PROGRAM_FIELDS]))
        conn.commit()
        return jsonify({"scholarship_id": cur.lastrowid}), 201


@app.route("/api/scholarships/<int:scholarship_id>", methods=["PUT"])
def update_scholarship(scholarship_id):
    clean, error = clean_program(json_body(), scales_by_id())
    if error:
        abort(400, error)
    with db() as (conn, cur):
        old = load_scholarship(cur, scholarship_id)
        if clean["grade_scale"] != old["grade_scale"]:
            cur.execute("SELECT COUNT(*) AS n FROM applicants"
                        " WHERE scholarship_id=%s", (scholarship_id,))
            if cur.fetchone()["n"] > 0:
                abort(400, "The grade scale cannot change once the program "
                           "has applicants. Delete them first or create a "
                           "new program")
        criteria_changed = any(not same_value(f, clean[f], old[f])
                               for f in CRITERIA_FIELDS)
        slots_changed = clean["available_slots"] != old["available_slots"]
        cur.execute(
            "UPDATE scholarship_programs SET "
            + ", ".join(f"{f}=%s" for f in PROGRAM_FIELDS)
            + " WHERE scholarship_id=%s",
            (*[clean[f] for f in PROGRAM_FIELDS], scholarship_id))
        # Old results no longer match the new rules, so clear them.
        if criteria_changed:
            cur.execute("DELETE FROM screening_results WHERE scholarship_id=%s",
                        (scholarship_id,))
        elif slots_changed:
            cur.execute(
                "DELETE rr FROM ranking_results rr JOIN screening_results sr"
                " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s",
                (scholarship_id,))
        conn.commit()
        return jsonify({"scholarship_id": scholarship_id,
                        "screening_cleared": criteria_changed,
                        "ranking_cleared": criteria_changed or slots_changed})


# ==================== SHAWN: ranking routes ====================

@app.route("/api/scholarships/<int:scholarship_id>/rank", methods=["POST"])
def rank_scholarship(scholarship_id):
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        if scholarship["status"] == "Closed":
            abort(400, "This program is closed. Reopen it to run ranking")
        cur.execute("SELECT COUNT(*) AS n FROM screening_results"
                    " WHERE scholarship_id=%s", (scholarship_id,))
        if cur.fetchone()["n"] == 0:
            abort(400, "Run screening before ranking")

        # Clear the previous ranking, so re-running is safe.
        cur.execute(
            "DELETE rr FROM ranking_results rr JOIN screening_results sr"
            " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s",
            (scholarship_id,))
        cur.execute(
            "SELECT sr.result_id, a.* FROM screening_results sr"
            " JOIN applicants a ON a.applicant_id = sr.applicant_id"
            " WHERE sr.scholarship_id=%s AND sr.eligible=1", (scholarship_id,))
        scored = [(a["result_id"], predict_priority(a, scholarship),
                   program_standing(a["gwa"], scholarship),
                   a["household_income"])
                  for a in cur.fetchall()]
        # Highest priority first. Equal scores: better GWA first (a higher
        # standing, whatever the program's scale), then lower household
        # income, then result_id so the order is always the same.
        scored.sort(key=lambda x: (-x[1], -x[2], float(x[3]), x[0]))

        slots = scholarship["available_slots"] or 0
        for rank, (result_id, score, _gwa, _income) in enumerate(scored, 1):
            status = "SHORTLIST" if rank <= slots else "WAITLIST"
            cur.execute(
                "INSERT INTO ranking_results"
                " (result_id, priority_score, rank_position, status)"
                " VALUES (%s,%s,%s,%s)", (result_id, score, rank, status))
        cur.execute("UPDATE scholarship_programs SET status='Ranking'"
                    " WHERE scholarship_id=%s", (scholarship_id,))
        conn.commit()
        shortlisted = min(len(scored), slots)
        return jsonify({"ranked_count": len(scored),
                        "shortlisted": shortlisted,
                        "waitlisted": len(scored) - shortlisted})


@app.route("/api/scholarships/<int:scholarship_id>/shortlist",
           methods=["GET"])
def get_shortlist(scholarship_id):
    with db() as (conn, cur):
        load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT a.applicant_id, a.full_name, rr.priority_score,"
            " rr.rank_position, rr.status FROM ranking_results rr"
            " JOIN screening_results sr ON sr.result_id = rr.result_id"
            " JOIN applicants a ON a.applicant_id = sr.applicant_id"
            " WHERE sr.scholarship_id=%s ORDER BY rr.rank_position",
            (scholarship_id,))
        return jsonify([json_safe(r) for r in cur.fetchall()])


def csv_safe(text):
    """Stop Excel from running a name such as =CMD() as a formula."""
    text = "" if text is None else str(text)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@app.route("/api/scholarships/<int:scholarship_id>/shortlist.csv",
           methods=["GET"])
def export_shortlist(scholarship_id):
    """Download the ranked list as a CSV file. The final decision is made by
    the administrator outside the system."""
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT rr.rank_position, a.full_name, rr.priority_score,"
            " rr.status, a.gwa, a.entrance_score, a.household_income,"
            " a.course, a.year_level, a.location FROM ranking_results rr"
            " JOIN screening_results sr ON sr.result_id = rr.result_id"
            " JOIN applicants a ON a.applicant_id = sr.applicant_id"
            " WHERE sr.scholarship_id=%s ORDER BY rr.rank_position",
            (scholarship_id,))
        rows = cur.fetchall()
    if not rows:
        abort(400, "Run ranking first. There is nothing to export yet")
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["rank", "full_name", "priority_score", "status", "grade_scale",
                     "gwa", "entrance_score", "household_income", "course",
                     "year_level", "location"])
    for r in rows:
        writer.writerow([r["rank_position"], csv_safe(r["full_name"]),
                         r["priority_score"], r["status"],
                         scholarship["grade_scale"], r["gwa"],
                         r["entrance_score"], r["household_income"],
                         r["course"], r["year_level"], r["location"]])
    filename = "shortlist_program_%d.csv" % scholarship_id
    return Response("﻿" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=" + filename})


@app.route("/api/scholarships/<int:scholarship_id>/applicants/"
           "<int:applicant_id>", methods=["DELETE"])
def delete_applicant(scholarship_id, applicant_id):
    """Remove one applicant and everything stored about them (screening
    reasons and ranking rows go with it). The old ranking no longer matches
    the remaining applicants, so it is cleared and must be run again."""
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        cur.execute("SELECT 1 FROM applicants WHERE applicant_id=%s"
                    " AND scholarship_id=%s", (applicant_id, scholarship_id))
        if cur.fetchone() is None:
            abort(404, "Applicant not found")
        cur.execute("DELETE FROM applicants WHERE applicant_id=%s",
                    (applicant_id,))
        cur.execute(
            "DELETE rr FROM ranking_results rr JOIN screening_results sr"
            " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s",
            (scholarship_id,))
        ranking_cleared = scholarship["status"] == "Ranking"
        if ranking_cleared:
            cur.execute("UPDATE scholarship_programs SET status='Screening'"
                        " WHERE scholarship_id=%s", (scholarship_id,))
        conn.commit()
        return jsonify({"deleted": applicant_id,
                        "ranking_cleared": ranking_cleared})


@app.route("/api/scholarships/<int:scholarship_id>/applicants/"
           "<int:applicant_id>/explanation", methods=["GET"])
def explain_applicant(scholarship_id, applicant_id):
    """Why this applicant got this priority score (UC: View Explanation)."""
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT sr.result_id, a.* FROM screening_results sr"
            " JOIN applicants a ON a.applicant_id = sr.applicant_id"
            " WHERE sr.scholarship_id=%s AND sr.eligible=1", (scholarship_id,))
        pool = cur.fetchall()
        applicant = next((a for a in pool
                          if a["applicant_id"] == applicant_id), None)
        if applicant is None:
            abort(404, "That applicant is not an eligible, screened "
                       "applicant of this program")
        cur.execute("SELECT priority_score, rank_position, status"
                    " FROM ranking_results WHERE result_id=%s",
                    (applicant["result_id"],))
        ranking = cur.fetchone()
        if ranking is None:
            abort(400, "Run ranking first")
        return jsonify({
            "applicant_id": applicant_id,
            "priority_score": float(ranking["priority_score"]),
            "rank_position": ranking["rank_position"],
            "status": ranking["status"],
            "compared_with": f"the average of {len(pool)} eligible applicants"
                             " in this program",
            "effects": explain_priority(applicant, pool, scholarship),
            "note": "Effects are in priority points. They show how this "
                    "applicant's inputs differ from the average and how the "
                    "model weighs that difference. The score is decision "
                    "support, not a probability of getting the scholarship.",
        })


# ==================== SHAWN: screening details route (Phase 2) ====================

@app.route("/api/scholarships/<int:scholarship_id>/screening",
           methods=["GET"])
def get_screening_details(scholarship_id):
    with db() as (conn, cur):
        load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT sr.result_id, a.applicant_id, a.full_name, sr.eligible"
            " FROM screening_results sr"
            " JOIN applicants a ON a.applicant_id = sr.applicant_id"
            " WHERE sr.scholarship_id=%s ORDER BY a.applicant_id",
            (scholarship_id,))
        out = []
        for r in cur.fetchall():
            cur.execute(
                "SELECT criterion_name, applicant_value, threshold_value, met"
                " FROM screening_reasons WHERE result_id=%s ORDER BY reason_id",
                (r["result_id"],))
            reasons = [{**x, "met": bool(x["met"])} for x in cur.fetchall()]
            out.append({"applicant_id": r["applicant_id"],
                        "full_name": r["full_name"],
                        "eligible": bool(r["eligible"]),
                        "reasons": reasons})
        return jsonify(out)


# ==================== SHAWN: import applicants from CSV / Excel ====================

IMPORT_COLUMNS = ["full_name", "gwa", "entrance_score", "household_income",
                  "course", "year_level", "location"]
MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 1000


def read_spreadsheet(upload):
    name = (upload.filename or "").lower()
    raw = upload.read()
    if len(raw) > MAX_IMPORT_BYTES:
        abort(400, "The file is larger than 2 MB")
    try:
        if name.endswith(".csv"):
            rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
        elif name.endswith(".xlsx"):
            book = openpyxl.load_workbook(io.BytesIO(raw), read_only=True,
                                          data_only=True)
            rows = [list(r) for r in book.active.iter_rows(values_only=True)]
        else:
            abort(400, "Upload a .csv or .xlsx file")
    except HTTPException:
        raise
    except Exception:
        abort(400, "The file could not be read. Save it again as .csv or .xlsx")
    return rows


@app.route("/api/scholarships/<int:scholarship_id>/applicants/import",
           methods=["POST"])
def import_applicants(scholarship_id):
    """Send the file as form-data field 'file'. By default this is a PREVIEW:
    nothing is saved. Send preview=false to save the valid rows."""
    preview = request.form.get("preview", "true").lower() != "false"
    upload = request.files.get("file")
    if upload is None:
        abort(400, "Attach a file in the 'file' field")
    rows = read_spreadsheet(upload)
    if not rows:
        abort(400, "The file is empty")

    header = [str(h or "").strip().lower().replace(" ", "_") for h in rows[0]]
    missing = [c for c in IMPORT_COLUMNS if c not in header]
    if missing:
        abort(400, "Missing column(s): " + ", ".join(missing))
    body = [r for r in rows[1:] if any(str(c or "").strip() for c in r)]
    if len(body) > MAX_IMPORT_ROWS:
        abort(400, f"More than {MAX_IMPORT_ROWS} rows. Split the file")

    valid, errors, seen = [], [], set()
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        scale = program_scale(program)
        for i, r in enumerate(rows[1:], start=2):  # spreadsheet row numbers
            if not any(str(c or "").strip() for c in r):
                continue
            record = {h: (r[j] if j < len(r) else None)
                      for j, h in enumerate(header)}
            clean, error = clean_applicant(record, scale)
            if error is None:
                key = (clean["full_name"].lower(), clean["course"],
                       clean["year_level"], clean["location"])
                if key in seen or applicant_exists(cur, scholarship_id, clean):
                    error = "Duplicate applicant"
                seen.add(key)
            if error:
                errors.append({"row": i, "error": error})
            else:
                valid.append(clean)
        if not preview and valid:
            cur.executemany(INSERT_APPLICANT,
                            [applicant_values(scholarship_id, a) for a in valid])
            conn.commit()
    return jsonify({
        "preview": preview,
        "total_rows": len(body),
        "valid_rows": len(valid),
        "imported": 0 if preview else len(valid),
        "errors": errors,
        "sample": valid[:5],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
