import csv
import io

from flask import Blueprint, Response, abort, jsonify

from db import db
from helpers import load_scholarship

exports_bp = Blueprint("exports", __name__)


def csv_safe(text):
    """Stop Excel from running a name such as =CMD() as a formula."""
    text = "" if text is None else str(text)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@exports_bp.route("/api/scholarships/<int:scholarship_id>/shortlist.csv",
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
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=" + filename})


CRITERIA_ORDER = ["GWA", "Entrance Score", "Income", "Field", "Year Level",
                  "Location"]


def csv_response(rows, filename):
    out = io.StringIO()
    csv.writer(out).writerows(rows)
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=" + filename})


@exports_bp.route("/api/scholarships/<int:scholarship_id>/applicants.csv",
                  methods=["GET"])
def export_applicants(scholarship_id):
    """Every applicant of the program with the screening and ranking result."""
    with db() as (conn, cur):
        load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT a.full_name, a.gwa, a.entrance_score, a.household_income,"
            " a.course, a.year_level, a.location, sr.eligible,"
            " rr.rank_position, rr.priority_score, rr.status"
            " FROM applicants a"
            " LEFT JOIN screening_results sr ON sr.applicant_id = a.applicant_id"
            " LEFT JOIN ranking_results rr ON rr.result_id = sr.result_id"
            " WHERE a.scholarship_id=%s ORDER BY a.applicant_id",
            (scholarship_id,))
        rows = cur.fetchall()
    if not rows:
        abort(400, "This program has no applicants to export")
    table = [["full_name", "gwa", "entrance_score", "household_income",
              "course", "year_level", "location", "screening", "rank",
              "priority_score", "shortlist_status"]]
    for r in rows:
        screening = ("Not screened" if r["eligible"] is None
                     else "Eligible" if r["eligible"] else "Not eligible")
        table.append([csv_safe(r["full_name"]), r["gwa"], r["entrance_score"],
                      r["household_income"], csv_safe(r["course"]),
                      r["year_level"], csv_safe(r["location"]), screening,
                      r["rank_position"] if r["rank_position"] is not None else "",
                      r["priority_score"] if r["priority_score"] is not None else "",
                      r["status"] or ""])
    return csv_response(table, "applicants_program_%d.csv" % scholarship_id)


@exports_bp.route("/api/scholarships/<int:scholarship_id>/screening-reasons.csv",
                  methods=["GET"])
def export_screening_reasons(scholarship_id):
    """One row per screened applicant with the six criteria: the applicant's
    value, the requirement and met or not met."""
    with db() as (conn, cur):
        load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT sr.result_id, sr.eligible, a.full_name,"
            " rs.criterion_name, rs.applicant_value, rs.threshold_value, rs.met"
            " FROM screening_results sr"
            " JOIN applicants a ON a.applicant_id = sr.applicant_id"
            " JOIN screening_reasons rs ON rs.result_id = sr.result_id"
            " WHERE sr.scholarship_id=%s ORDER BY a.applicant_id, rs.reason_id",
            (scholarship_id,))
        rows = cur.fetchall()
    if not rows:
        abort(400, "Run screening first. There are no results to export yet")
    people = {}
    for r in rows:
        person = people.setdefault(r["result_id"], {
            "name": r["full_name"], "eligible": r["eligible"], "c": {}})
        person["c"][r["criterion_name"]] = r
    header = ["full_name", "screening"]
    for c in CRITERIA_ORDER:
        header += [f"{c} - applicant", f"{c} - required", f"{c} - result"]
    table = [header]
    for person in people.values():
        line = [csv_safe(person["name"]),
                "Eligible" if person["eligible"] else "Not eligible"]
        for c in CRITERIA_ORDER:
            x = person["c"].get(c)
            line += ([csv_safe(x["applicant_value"]), csv_safe(x["threshold_value"]),
                      "Met" if x["met"] else "Not met"] if x else ["", "", ""])
        table.append(line)
    return csv_response(table, "screening_reasons_program_%d.csv" % scholarship_id)


@exports_bp.route("/api/scholarships/<int:scholarship_id>/screening-summary",
                  methods=["GET"])
def screening_summary(scholarship_id):
    """How many applicants failed each criterion (an applicant who fails
    several counts once under each) and how many missed by one rule only."""
    with db() as (conn, cur):
        load_scholarship(cur, scholarship_id)
        cur.execute("SELECT COUNT(*) AS n FROM applicants WHERE scholarship_id=%s",
                    (scholarship_id,))
        total = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n, COALESCE(SUM(eligible),0) AS ok"
                    " FROM screening_results WHERE scholarship_id=%s",
                    (scholarship_id,))
        row = cur.fetchone()
        screened, eligible = row["n"], int(row["ok"])
        cur.execute(
            "SELECT rs.criterion_name, COUNT(*) AS n FROM screening_reasons rs"
            " JOIN screening_results sr ON sr.result_id = rs.result_id"
            " WHERE sr.scholarship_id=%s AND rs.met=0"
            " GROUP BY rs.criterion_name", (scholarship_id,))
        failed = {r["criterion_name"]: r["n"] for r in cur.fetchall()}
        cur.execute(
            "SELECT COUNT(*) AS n FROM (SELECT sr.result_id"
            " FROM screening_results sr JOIN screening_reasons rs"
            " ON rs.result_id = sr.result_id"
            " WHERE sr.scholarship_id=%s AND rs.met=0"
            " GROUP BY sr.result_id HAVING COUNT(*)=1) t", (scholarship_id,))
        near = cur.fetchone()["n"]
    return jsonify({
        "total": total, "screened": screened, "unscreened": total - screened,
        "eligible": eligible, "ineligible": screened - eligible,
        "failures": [{"criterion": c, "failed": failed.get(c, 0)}
                     for c in CRITERIA_ORDER],
        "missed_by_one_rule": near,
    })
