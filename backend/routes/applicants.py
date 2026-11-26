import csv
import io

import openpyxl
from flask import Blueprint, abort, jsonify, request
from werkzeug.exceptions import HTTPException

from db import db, json_safe
from helpers import (has_ranking, json_body, load_applicant_requirements_map,
                     load_program_requirements, load_scholarship,
                     normalize_req_list, program_scale, renumber_ranking,
                     require_open_program, save_applicant_requirements,
                     screen_one, write_ranking)
from validation import clean_applicant, clean_applicant_import

applicants_bp = Blueprint("applicants", __name__)

INSERT_APPLICANT = (
    "INSERT INTO applicants (scholarship_id, full_name, gwa, entrance_score,"
    " household_income, course, year_level, location)"
    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")

APPLICANT_RESTORE_COLS = ("full_name, gwa, entrance_score, household_income,"
                          " course, year_level, location")
MAX_BULK_IDS = 5000

IMPORT_COLUMNS = ["full_name", "gwa", "entrance_score", "household_income",
                  "course", "year_level", "location"]
MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 1000


def applicant_exists(cur, scholarship_id, a, exclude_id=None):
    cur.execute(
        "SELECT 1 FROM applicants WHERE scholarship_id=%s"
        " AND LOWER(full_name)=LOWER(%s) AND course=%s AND year_level=%s"
        " AND location=%s AND applicant_id<>%s LIMIT 1",
        (scholarship_id, a["full_name"], a["course"], a["year_level"],
         a["location"], exclude_id or 0))
    return cur.fetchone() is not None


def applicant_values(scholarship_id, a):
    return (scholarship_id, a["full_name"], a["gwa"], a["entrance_score"],
            a["household_income"], a["course"], a["year_level"], a["location"])


def selected_ids(data, cur, scholarship_id):
    ids = data.get("ids")
    if not isinstance(ids, list) or not ids:
        abort(400, "Select at least one applicant")
    if len(ids) > MAX_BULK_IDS:
        abort(400, f"Select at most {MAX_BULK_IDS} applicants at a time")
    try:
        ids = sorted({int(i) for i in ids})
    except (TypeError, ValueError):
        abort(400, "The selection was not valid. Refresh the page and try again")
    marks = ",".join(["%s"] * len(ids))
    cur.execute("SELECT applicant_id FROM applicants WHERE scholarship_id=%s"
                f" AND applicant_id IN ({marks})", (scholarship_id, *ids))
    if len(cur.fetchall()) != len(ids):
        abort(404, "One or more selected applicants were not found in this "
                   "program")
    return ids


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


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants",
                     methods=["POST"])
def add_applicant(scholarship_id):
    data = json_body()
    submitted = normalize_req_list(data.get("submitted_requirements"))
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        require_open_program(program, "add applicants")
        clean, error = clean_applicant(data, program_scale(program))
        if error:
            abort(400, error)
        if applicant_exists(cur, scholarship_id, clean):
            abort(409, "This applicant is already in this program")
        cur.execute(INSERT_APPLICANT, applicant_values(scholarship_id, clean))
        new_id = cur.lastrowid
        if submitted:
            save_applicant_requirements(cur, new_id, submitted)
        conn.commit()
        return jsonify({"applicant_id": new_id}), 201


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants",
                     methods=["GET"])
def list_applicants(scholarship_id):
    with db() as (conn, cur):
        load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT applicant_id, full_name, gwa, entrance_score,"
            " household_income, course, year_level, location"
            " FROM applicants WHERE scholarship_id=%s ORDER BY applicant_id",
            (scholarship_id,))
        rows = [json_safe(r) for r in cur.fetchall()]
        req_map = load_applicant_requirements_map(
            cur, [r["applicant_id"] for r in rows]
        )
        for r in rows:
            r["submitted_requirements"] = req_map.get(r["applicant_id"], [])
        return jsonify(rows)


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants/"
                     "<int:applicant_id>", methods=["PUT"])
def update_applicant(scholarship_id, applicant_id):
    data = json_body()
    has_reqs = "submitted_requirements" in data
    submitted = normalize_req_list(data.get("submitted_requirements")) if has_reqs else None
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        require_open_program(program, "edit applicants")
        cur.execute("SELECT 1 FROM applicants WHERE applicant_id=%s"
                    " AND scholarship_id=%s", (applicant_id, scholarship_id))
        if cur.fetchone() is None:
            abort(404, "Applicant not found")
        clean, error = clean_applicant(data, program_scale(program))
        if error:
            abort(400, error)
        if applicant_exists(cur, scholarship_id, clean, applicant_id):
            abort(409, "Another applicant in this program already has the "
                       "same name, course, year level and location")
        cur.execute(
            "UPDATE applicants SET full_name=%s, gwa=%s, entrance_score=%s,"
            " household_income=%s, course=%s, year_level=%s, location=%s"
            " WHERE applicant_id=%s",
            (clean["full_name"], clean["gwa"], clean["entrance_score"],
             clean["household_income"], clean["course"], clean["year_level"],
             clean["location"], applicant_id))
        if has_reqs:
            save_applicant_requirements(cur, applicant_id, submitted)
        cur.execute("SELECT 1 FROM screening_results WHERE applicant_id=%s",
                    (applicant_id,))
        was_screened = cur.fetchone() is not None
        cur.execute("DELETE FROM screening_results WHERE applicant_id=%s",
                    (applicant_id,))
        ranked = has_ranking(cur, scholarship_id)
        if ranked:
            renumber_ranking(cur, program)
        conn.commit()
        return jsonify({"updated": applicant_id,
                        "was_screened": was_screened,
                        "program_ranked": ranked})


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants/"
                     "<int:applicant_id>", methods=["DELETE"])
def delete_applicant(scholarship_id, applicant_id):
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        require_open_program(scholarship, "delete applicants")
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


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants/bulk-delete",
                     methods=["POST"])
def bulk_delete_applicants(scholarship_id):
    data = json_body()
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        require_open_program(scholarship, "delete applicants")
        delete_all = bool(data.get("all"))
        if delete_all:
            if str(data.get("confirm_name") or "").strip() != \
                    scholarship["scholarship_name"]:
                abort(400, "Type the program name exactly to delete all "
                           "applicants")
            cur.execute(f"SELECT applicant_id, {APPLICANT_RESTORE_COLS} FROM applicants"
                        " WHERE scholarship_id=%s ORDER BY applicant_id",
                        (scholarship_id,))
        else:
            ids = selected_ids(data, cur, scholarship_id)
            marks = ",".join(["%s"] * len(ids))
            cur.execute(f"SELECT applicant_id, {APPLICANT_RESTORE_COLS} FROM applicants"
                        f" WHERE applicant_id IN ({marks})"
                        " ORDER BY applicant_id", tuple(ids))
        rows = cur.fetchall()
        if not rows:
            abort(400, "This program has no applicants to delete")
        req_map = load_applicant_requirements_map(
            cur, [r["applicant_id"] for r in rows]
        )
        restore = []
        for r in rows:
            item = json_safe({k: r[k] for k in (
                "full_name", "gwa", "entrance_score", "household_income",
                "course", "year_level", "location",
            )})
            reqs_for_row = req_map.get(r["applicant_id"], [])
            if reqs_for_row:
                item["submitted_requirements"] = reqs_for_row
            restore.append(item)
        if delete_all:
            cur.execute("DELETE FROM applicants WHERE scholarship_id=%s",
                        (scholarship_id,))
        else:
            cur.execute(f"DELETE FROM applicants WHERE applicant_id IN ({marks})",
                        tuple(ids))
        cur.execute(
            "DELETE rr FROM ranking_results rr JOIN screening_results sr"
            " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s",
            (scholarship_id,))
        ranking_cleared = scholarship["status"] == "Ranking"
        if delete_all and scholarship["status"] in ("Screening", "Ranking"):
            cur.execute("UPDATE scholarship_programs SET status='Open'"
                        " WHERE scholarship_id=%s", (scholarship_id,))
        elif ranking_cleared:
            cur.execute("UPDATE scholarship_programs SET status='Screening'"
                        " WHERE scholarship_id=%s", (scholarship_id,))
        conn.commit()
        return jsonify({"deleted": len(restore),
                        "ranking_cleared": ranking_cleared,
                        "restore": restore})


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants/restore",
                     methods=["POST"])
def restore_applicants(scholarship_id):
    data = json_body()
    items = data.get("applicants")
    if not isinstance(items, list) or not items:
        abort(400, "There is nothing to restore")
    if len(items) > MAX_BULK_IDS:
        abort(400, f"Restore at most {MAX_BULK_IDS} applicants at a time")
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        require_open_program(program, "restore applicants")
        scale = program_scale(program)
        restored = skipped = 0
        for item in items:
            clean, error = clean_applicant(item, scale)
            if error or applicant_exists(cur, scholarship_id, clean):
                skipped += 1
                continue
            cur.execute(INSERT_APPLICANT, applicant_values(scholarship_id, clean))
            new_id = cur.lastrowid
            if isinstance(item, dict) and item.get("submitted_requirements"):
                reqs_list = normalize_req_list(item.get("submitted_requirements"))
                if reqs_list:
                    save_applicant_requirements(cur, new_id, reqs_list)
            restored += 1
        conn.commit()
        return jsonify({"restored": restored, "skipped": skipped})


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants/screen-selected",
                     methods=["POST"])
def screen_selected_applicants(scholarship_id):
    data = json_body()
    want_rank = bool(data.get("rank"))
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        if scholarship["status"] == "Closed":
            abort(400, "This program is closed. Reopen it to run screening")
        ids = selected_ids(data, cur, scholarship_id)
        if want_rank and not has_ranking(cur, scholarship_id):
            abort(400, "This program has not been ranked yet. Run ranking "
                       "for the whole program first")
        marks = ",".join(["%s"] * len(ids))
        cur.execute(f"DELETE FROM screening_results WHERE applicant_id IN ({marks})",
                    tuple(ids))
        cur.execute(f"SELECT * FROM applicants WHERE applicant_id IN ({marks})",
                    tuple(ids))
        applicants = cur.fetchall()
        req_labels = load_program_requirements(cur, scholarship_id)
        submitted_map = (load_applicant_requirements_map(cur, ids)
                         if req_labels else {})
        eligible = sum(
            1 for a in applicants
            if screen_one(cur, a, scholarship, req_labels,
                          submitted_map.get(a["applicant_id"], []))
        )
        if want_rank:
            write_ranking(cur, scholarship)
            cur.execute("UPDATE scholarship_programs SET status='Ranking'"
                        " WHERE scholarship_id=%s", (scholarship_id,))
        elif scholarship["status"] == "Open":
            cur.execute("UPDATE scholarship_programs SET status='Screening'"
                        " WHERE scholarship_id=%s", (scholarship_id,))
        conn.commit()
        return jsonify({"screened": len(ids), "eligible": eligible,
                        "ineligible": len(ids) - eligible, "ranked": want_rank})


def _extract_import_requirements(raw_headers, row_cells, record, prog_reqs):
    """Extract submitted custom prerequisites from optional spreadsheet columns:
    either a 'submitted_requirements' column or individual columns matching the
    program's additional_requirements with truthy markers (yes/1/true/submitted)."""
    reqs = normalize_req_list(record.get("submitted_requirements"))
    if prog_reqs:
        truthy = {"1", "yes", "y", "true", "submitted", "verified", "ok", "x", "✓"}
        prog_by_lower = {r.strip().lower(): r for r in prog_reqs if r.strip()}
        for j, raw_h in enumerate(raw_headers):
            col_clean = str(raw_h or "").strip().lower()
            col_norm = col_clean.replace("_", " ")
            matched = prog_by_lower.get(col_clean) or prog_by_lower.get(col_norm)
            if matched and j < len(row_cells):
                cell_val = str(row_cells[j] or "").strip().lower()
                if cell_val in truthy:
                    reqs.append(matched)
    return normalize_req_list(reqs)


@applicants_bp.route("/api/scholarships/<int:scholarship_id>/applicants/import",
                     methods=["POST"])
def import_applicants(scholarship_id):
    preview = request.form.get("preview", "true").lower() != "false"
    upload = request.files.get("file")
    if upload is None:
        abort(400, "Choose a .csv or .xlsx file to import")
    rows = read_spreadsheet(upload)
    if not rows:
        abort(400, "The file is empty")

    raw_headers = [str(h or "").strip() for h in rows[0]]
    header = [h.lower().replace(" ", "_") for h in raw_headers]
    missing = [c for c in IMPORT_COLUMNS if c not in header]
    if missing:
        abort(400, "Missing column(s): " + ", ".join(missing))
    body = [r for r in rows[1:] if any(str(c or "").strip() for c in r)]
    if len(body) > MAX_IMPORT_ROWS:
        abort(400, f"More than {MAX_IMPORT_ROWS} rows. Split the file")

    valid, valid_reqs, preview_items, errors, seen = [], [], [], [], set()
    normalized_count = 0
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        require_open_program(program, "import applicants")
        scale = program_scale(program)
        prog_reqs = load_program_requirements(cur, scholarship_id)
        cur.execute(
            "SELECT full_name, course, year_level, location"
            " FROM applicants WHERE scholarship_id=%s",
            (scholarship_id,),
        )
        existing_keys = {
            (r["full_name"].lower(), r["course"], r["year_level"], r["location"])
            for r in cur.fetchall()
        }
        for i, r in enumerate(rows[1:], start=2):
            if not any(str(c or "").strip() for c in r):
                continue
            record = {h: (r[j] if j < len(r) else None)
                      for j, h in enumerate(header)}
            clean, corrections, error = clean_applicant_import(record, scale)
            if error is None:
                key = (clean["full_name"].lower(), clean["course"],
                       clean["year_level"], clean["location"])
                if key in seen or key in existing_keys:
                    error = "Duplicate applicant"
                seen.add(key)
            if error:
                rec_out = {
                    c: ("" if record.get(c) is None else str(record.get(c)))
                    for c in IMPORT_COLUMNS
                }
                if "submitted_requirements" in record:
                    rec_out["submitted_requirements"] = (
                        "" if record.get("submitted_requirements") is None
                        else str(record.get("submitted_requirements"))
                    )
                errors.append({"row": i, "error": error, "record": rec_out})
            else:
                row_reqs = _extract_import_requirements(
                    raw_headers, r, record, prog_reqs
                )
                if corrections:
                    normalized_count += 1
                valid.append(clean)
                valid_reqs.append(row_reqs)
                sample_row = dict(clean)
                if row_reqs:
                    sample_row["submitted_requirements"] = row_reqs
                if corrections:
                    sample_row["corrections"] = corrections
                preview_items.append(sample_row)
        if not preview and valid:
            for a, reqs_list in zip(valid, valid_reqs):
                cur.execute(INSERT_APPLICANT,
                            applicant_values(scholarship_id, a))
                new_id = cur.lastrowid
                if reqs_list:
                    save_applicant_requirements(cur, new_id, reqs_list)
            conn.commit()
    return jsonify({
        "preview": preview,
        "total_rows": len(body),
        "valid_rows": len(valid),
        "normalized_count": normalized_count,
        "imported": 0 if preview else len(valid),
        "errors": errors,
        "sample": preview_items[:5],
    })
