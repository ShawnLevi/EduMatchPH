from flask import Blueprint, abort, jsonify, request

from db import db
from helpers import (CRITERIA_FIELDS, PROGRAM_FIELDS, current_org,
                     current_role, json_body, load_program_requirements,
                     load_programs_requirements_map, load_scholarship,
                     normalize_req_list, program_json, record_audit,
                     require_roles, same_value, save_program_requirements,
                     scales_by_id)
from validation import clean_program

programs_bp = Blueprint("programs", __name__)


@programs_bp.route("/api/scholarships", methods=["GET"])
def list_scholarships():
    req_org = request.args.get("organization_id")
    is_super = current_role() == "super_admin"
    if not is_super:
        org = req_org or current_org()
        if org != current_org():
            abort(403, "You can only view your own organization")
    else:
        org = req_org
    include_archived = request.args.get("include_archived") == "1"
    with db() as (conn, cur):
        sql = (
            "SELECT sp.*, o.organization_name,"
            " gs.label AS grade_scale_label,"
            " gs.higher_is_better AS higher_is_better"
            " FROM scholarship_programs sp"
            " JOIN organizations o ON o.organization_id = sp.organization_id"
            " JOIN grade_scales gs ON gs.scale_id = sp.grade_scale"
            " WHERE 1=1"
        )
        params = []
        if org:
            sql += " AND sp.organization_id=%s"
            params.append(org)
        if not include_archived:
            sql += " AND sp.is_archived = 0"
        sql += " ORDER BY sp.organization_id, sp.scholarship_id"
        cur.execute(sql, tuple(params))
        raw_rows = cur.fetchall()
        req_map = load_programs_requirements_map(
            cur, [r["scholarship_id"] for r in raw_rows]
        )
        rows = [program_json(r, req_map.get(r["scholarship_id"], []))
                for r in raw_rows]
        for r in rows:
            r["is_archived"] = bool(r["is_archived"])
        return jsonify(rows)


@programs_bp.route("/api/scholarships/<int:scholarship_id>", methods=["GET"])
def get_scholarship(scholarship_id):
    with db() as (conn, cur):
        row = load_scholarship(cur, scholarship_id)
        reqs = load_program_requirements(cur, scholarship_id)
        return jsonify(program_json(row, reqs))


@programs_bp.route("/api/scholarships", methods=["POST"])
def create_scholarship():
    body = json_body()
    clean, error = clean_program(body, scales_by_id())
    if error:
        abort(400, error)
    reqs = normalize_req_list(body.get("additional_requirements"))
    with db() as (conn, cur):
        cur.execute(
            "INSERT INTO scholarship_programs (organization_id, "
            + ", ".join(PROGRAM_FIELDS) + ") VALUES (%s,"
            + ",".join(["%s"] * len(PROGRAM_FIELDS)) + ")",
            (current_org(), *[clean[f] for f in PROGRAM_FIELDS]))
        new_id = cur.lastrowid
        if reqs:
            save_program_requirements(cur, new_id, reqs)
        record_audit(cur, "PROGRAM_CREATE", "scholarship", new_id,
                     f"Created program {clean['scholarship_name']}")
        conn.commit()
        return jsonify({"scholarship_id": new_id}), 201


@programs_bp.route("/api/scholarships/<int:scholarship_id>", methods=["PUT"])
def update_scholarship(scholarship_id):
    body = json_body()
    clean, error = clean_program(body, scales_by_id())
    if error:
        abort(400, error)
    has_reqs_field = "additional_requirements" in body
    new_reqs = normalize_req_list(body.get("additional_requirements")) if has_reqs_field else None
    with db() as (conn, cur):
        old = load_scholarship(cur, scholarship_id)
        old_reqs = load_program_requirements(cur, scholarship_id)
        if clean["grade_scale"] != old["grade_scale"]:
            cur.execute("SELECT COUNT(*) AS n FROM applicants"
                        " WHERE scholarship_id=%s", (scholarship_id,))
            if cur.fetchone()["n"] > 0:
                abort(400, "The grade scale cannot change once the program "
                           "has applicants. Delete them first or create a "
                           "new program")
        reqs_changed = has_reqs_field and (new_reqs != old_reqs)
        criteria_changed = reqs_changed or any(
            not same_value(f, clean[f], old[f]) for f in CRITERIA_FIELDS
        )
        slots_changed = clean["available_slots"] != old["available_slots"]
        cur.execute(
            "UPDATE scholarship_programs SET "
            + ", ".join(f"{f}=%s" for f in PROGRAM_FIELDS)
            + " WHERE scholarship_id=%s",
            (*[clean[f] for f in PROGRAM_FIELDS], scholarship_id))
        if has_reqs_field:
            save_program_requirements(cur, scholarship_id, new_reqs)
        if criteria_changed:
            cur.execute("DELETE FROM screening_results WHERE scholarship_id=%s",
                        (scholarship_id,))
        elif slots_changed:
            cur.execute(
                "DELETE rr FROM ranking_results rr JOIN screening_results sr"
                " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s",
                (scholarship_id,))
        record_audit(cur, "PROGRAM_UPDATE", "scholarship", scholarship_id,
                     f"Updated program {clean['scholarship_name']}")
        conn.commit()
        return jsonify({"scholarship_id": scholarship_id,
                        "screening_cleared": criteria_changed,
                        "ranking_cleared": criteria_changed or slots_changed})


@programs_bp.route("/api/scholarships/<int:scholarship_id>", methods=["DELETE"])
def delete_or_archive_scholarship(scholarship_id):
    """Archive a program that already has applicants (setting is_archived=1 and
    status='Closed'), or permanently delete it when empty or ?permanent=true."""
    require_roles("super_admin", "owner")
    permanent = request.args.get("permanent", "").lower() == "true"
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        cur.execute("SELECT COUNT(*) AS n FROM applicants"
                    " WHERE scholarship_id=%s", (scholarship_id,))
        has_applicants = cur.fetchone()["n"] > 0
        if permanent or not has_applicants:
            cur.execute("DELETE FROM scholarship_programs"
                        " WHERE scholarship_id=%s", (scholarship_id,))
            record_audit(cur, "PROGRAM_DELETE", "scholarship", scholarship_id,
                         f"Deleted program {program['scholarship_name']}")
            conn.commit()
            return jsonify({"deleted": scholarship_id, "archived": False})
        cur.execute(
            "UPDATE scholarship_programs SET is_archived=1, status='Closed'"
            " WHERE scholarship_id=%s", (scholarship_id,))
        record_audit(cur, "PROGRAM_ARCHIVE", "scholarship", scholarship_id,
                     f"Archived program {program['scholarship_name']}")
        conn.commit()
        return jsonify({"archived": scholarship_id, "deleted": False})


@programs_bp.route("/api/scholarships/<int:scholarship_id>/restore", methods=["POST"])
def restore_scholarship(scholarship_id):
    require_roles("super_admin", "owner")
    with db() as (conn, cur):
        program = load_scholarship(cur, scholarship_id)
        cur.execute(
            "UPDATE scholarship_programs SET is_archived=0, status='Open'"
            " WHERE scholarship_id=%s", (scholarship_id,))
        record_audit(cur, "PROGRAM_RESTORE", "scholarship", scholarship_id,
                     f"Restored archived program {program['scholarship_name']}")
        conn.commit()
        return jsonify({"restored": scholarship_id})
