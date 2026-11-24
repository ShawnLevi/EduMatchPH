from flask import abort, request, session

from db import db, json_safe
from eligibility import check_eligibility
from ranking import predict_priority, program_standing


def current_org():
    return session["organization_id"]


def current_role():
    return session.get("role", "admin")


def require_roles(*roles):
    if current_role() not in roles:
        abort(403, "You do not have permission to perform this action")


def require_open_program(program, action="modify applicants"):
    if program["status"] == "Closed":
        abort(400, f"This program is closed. Reopen it before you {action}")


def record_audit(cur, action, target_type=None, target_id=None, details=None,
                 org_id=None, admin_id=None):
    cur.execute(
        "INSERT INTO audit_logs"
        " (organization_id, admin_id, action, target_type, target_id, details)"
        " VALUES (%s,%s,%s,%s,%s,%s)",
        (org_id if org_id is not None else session.get("organization_id"),
         admin_id if admin_id is not None else session.get("admin_id"),
         action, target_type,
         str(target_id) if target_id is not None else None,
         details[:255] if details else None),
    )


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
        abort(400, "The request was incomplete. Refresh the page and try again")
    return data


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


SCHOLARSHIP_COLS = [
    "scholarship_id", "organization_id", "scholarship_name",
    "provider", "grade_scale", "gwa_limit", "income_cap",
    "eligible_field", "eligible_years", "location_req", "min_entrance",
    "available_slots", "status", "is_archived", "application_deadline",
]
SCHOLARSHIP_COLUMNS = ", ".join(SCHOLARSHIP_COLS)

PROGRAM_FIELDS = [
    "scholarship_name", "provider", "grade_scale", "gwa_limit",
    "income_cap", "eligible_field", "eligible_years", "location_req",
    "min_entrance", "available_slots", "status", "application_deadline",
]
CRITERIA_FIELDS = [
    "grade_scale", "gwa_limit", "income_cap", "eligible_field",
    "eligible_years", "location_req", "min_entrance",
]


def program_json(row):
    out = json_safe({k: row[k] for k in SCHOLARSHIP_COLS})
    out["grade_scale_label"] = row["grade_scale_label"]
    out["higher_is_better"] = bool(row["higher_is_better"])
    out["is_archived"] = bool(row.get("is_archived", 0))
    return out


def same_value(field, new, old):
    if field in ("gwa_limit", "income_cap"):  # Decimal vs float
        return float(new) == float(old)
    return str(new) == str(old)


def screen_one(cur, applicant, scholarship):
    """Check one applicant against the six rules and store the result and the
    reason for each criterion. Any earlier result for this applicant must be
    removed first by the caller. Returns True when the applicant is eligible."""
    is_eligible, checks = check_eligibility(applicant, scholarship)
    cur.execute(
        "INSERT INTO screening_results"
        " (applicant_id, scholarship_id, eligible) VALUES (%s,%s,%s)",
        (applicant["applicant_id"], scholarship["scholarship_id"],
         is_eligible))
    result_id = cur.lastrowid
    for name, (met, aval, tval) in checks.items():
        cur.execute(
            "INSERT INTO screening_reasons (result_id, criterion_name,"
            " applicant_value, threshold_value, met)"
            " VALUES (%s,%s,%s,%s,%s)",
            (result_id, name, str(aval), str(tval), met))
    return is_eligible


def write_ranking(cur, scholarship):
    """Score every eligible applicant of the program and store the ranking,
    replacing any earlier one. Returns (ranked_count, shortlisted_count)."""
    scholarship_id = scholarship["scholarship_id"]
    cur.execute(
        "DELETE rr FROM ranking_results rr JOIN screening_results sr"
        " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s",
        (scholarship_id,))
    cur.execute(
        "SELECT sr.result_id, a.* FROM screening_results sr"
        " JOIN applicants a ON a.applicant_id = sr.applicant_id"
        " WHERE sr.scholarship_id=%s AND sr.eligible=1", (scholarship_id,))
    import sys
    _predict = getattr(sys.modules.get("app"), "predict_priority",
                       predict_priority)
    scored = [(a["result_id"], _predict(a, scholarship),
               program_standing(a["gwa"], scholarship),
               a["household_income"])
              for a in cur.fetchall()]
    scored.sort(key=lambda x: (-x[1], -x[2], float(x[3]), x[0]))
    slots = scholarship["available_slots"] or 0
    for rank, (result_id, score, _gwa, _income) in enumerate(scored, 1):
        status = "SHORTLIST" if rank <= slots else "WAITLIST"
        cur.execute(
            "INSERT INTO ranking_results"
            " (result_id, priority_score, rank_position, status)"
            " VALUES (%s,%s,%s,%s)", (result_id, score, rank, status))
    return len(scored), min(len(scored), slots)


def has_ranking(cur, scholarship_id):
    cur.execute(
        "SELECT 1 FROM ranking_results rr JOIN screening_results sr"
        " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s LIMIT 1",
        (scholarship_id,))
    return cur.fetchone() is not None
