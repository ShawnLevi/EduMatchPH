import re

from flask import abort, request, session

from db import db, json_safe
from eligibility import check_eligibility
from ranking import predict_priorities, predict_priority, program_standing


def normalize_req_list(raw):
    """Turn a list (or comma-separated string) into deduplicated requirement labels."""
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [x.strip() for x in raw.split(",")]
    elif isinstance(raw, (list, tuple)):
        items = [str(x or "").strip() for x in raw]
    else:
        return []
    out, seen = [], set()
    for item in items:
        if not item or len(item) > 120:
            continue
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _ensure_requirement_type(cur, label):
    cur.execute(
        "SELECT requirement_id FROM requirement_types"
        " WHERE LOWER(label)=LOWER(%s) LIMIT 1",
        (label,),
    )
    row = cur.fetchone()
    if row:
        return row["requirement_id"]
    base = re.sub(r"[^A-Z0-9]+", "_", label.upper()).strip("_")[:32] or "REQ"
    code = f"C_{base}"
    cur.execute("SELECT requirement_id FROM requirement_types WHERE code=%s", (code,))
    if cur.fetchone():
        suffix = 2
        while True:
            cand = f"{code[:36]}_{suffix}"
            cur.execute("SELECT 1 FROM requirement_types WHERE code=%s", (cand,))
            if not cur.fetchone():
                code = cand
                break
            suffix += 1
    cur.execute(
        "INSERT INTO requirement_types (code, label, value_kind, is_sensitive)"
        " VALUES (%s, %s, 'YES_NO', 0)",
        (code, label),
    )
    return cur.lastrowid


def load_program_requirements(cur, scholarship_id):
    cur.execute(
        "SELECT rt.label FROM program_requirements pr"
        " JOIN requirement_types rt ON rt.requirement_id = pr.requirement_id"
        " WHERE pr.scholarship_id=%s AND pr.is_mandatory=1"
        " ORDER BY pr.program_req_id",
        (scholarship_id,),
    )
    return [r["label"] for r in cur.fetchall()]


def load_programs_requirements_map(cur, scholarship_ids):
    if not scholarship_ids:
        return {}
    marks = ",".join(["%s"] * len(scholarship_ids))
    cur.execute(
        "SELECT pr.scholarship_id, rt.label FROM program_requirements pr"
        " JOIN requirement_types rt ON rt.requirement_id = pr.requirement_id"
        f" WHERE pr.scholarship_id IN ({marks}) AND pr.is_mandatory=1"
        " ORDER BY pr.program_req_id",
        tuple(scholarship_ids),
    )
    out = {sid: [] for sid in scholarship_ids}
    for r in cur.fetchall():
        out.setdefault(r["scholarship_id"], []).append(r["label"])
    return out


def save_program_requirements(cur, scholarship_id, labels):
    cur.execute("DELETE FROM program_requirements WHERE scholarship_id=%s",
                (scholarship_id,))
    for label in normalize_req_list(labels):
        req_id = _ensure_requirement_type(cur, label)
        cur.execute(
            "INSERT INTO program_requirements (scholarship_id, requirement_id, is_mandatory)"
            " VALUES (%s, %s, 1)",
            (scholarship_id, req_id),
        )


def load_applicant_requirements_map(cur, applicant_ids):
    if not applicant_ids:
        return {}
    marks = ",".join(["%s"] * len(applicant_ids))
    cur.execute(
        "SELECT ar.applicant_id, rt.label FROM applicant_requirements ar"
        " JOIN requirement_types rt ON rt.requirement_id = ar.requirement_id"
        f" WHERE ar.applicant_id IN ({marks}) AND ar.status IN ('SUBMITTED','VERIFIED')"
        " ORDER BY ar.applicant_req_id",
        tuple(applicant_ids),
    )
    out = {aid: [] for aid in applicant_ids}
    for r in cur.fetchall():
        out.setdefault(r["applicant_id"], []).append(r["label"])
    return out


def save_applicant_requirements(cur, applicant_id, labels):
    cur.execute("DELETE FROM applicant_requirements WHERE applicant_id=%s",
                (applicant_id,))
    for label in normalize_req_list(labels):
        req_id = _ensure_requirement_type(cur, label)
        cur.execute(
            "INSERT INTO applicant_requirements (applicant_id, requirement_id, status)"
            " VALUES (%s, %s, 'VERIFIED')",
            (applicant_id, req_id),
        )


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
    """The program, scoped to the logged-in organization (super_admin sees all)."""
    sql = (
        "SELECT sp.*, o.organization_name,"
        " gs.label AS grade_scale_label,"
        " gs.min_value AS scale_min, gs.max_value AS scale_max,"
        " gs.best_value AS scale_best, gs.passing_value AS scale_passing,"
        " gs.higher_is_better AS higher_is_better"
        " FROM scholarship_programs sp"
        " JOIN organizations o ON o.organization_id = sp.organization_id"
        " JOIN grade_scales gs ON gs.scale_id = sp.grade_scale"
        " WHERE sp.scholarship_id=%s"
    )
    params = [scholarship_id]
    if current_role() != "super_admin":
        sql += " AND sp.organization_id=%s"
        params.append(current_org())
    cur.execute(sql, tuple(params))
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


def program_json(row, additional_requirements=None):
    out = json_safe({k: row[k] for k in SCHOLARSHIP_COLS})
    if "organization_name" in row:
        out["organization_name"] = row["organization_name"]
    out["grade_scale_label"] = row["grade_scale_label"]
    out["higher_is_better"] = bool(row["higher_is_better"])
    out["is_archived"] = bool(row.get("is_archived", 0))
    out["additional_requirements"] = (
        list(additional_requirements) if additional_requirements is not None else []
    )
    return out


def same_value(field, new, old):
    if field in ("gwa_limit", "income_cap"):  # Decimal vs float
        return float(new) == float(old)
    return str(new) == str(old)


def screen_one(cur, applicant, scholarship, required_reqs=None,
               submitted_reqs=None):
    """Check one applicant against the six rules + program prerequisites and
    store the result and criterion reasons. Returns True when eligible."""
    if required_reqs is None:
        required_reqs = load_program_requirements(cur, scholarship["scholarship_id"])
    if submitted_reqs is None and required_reqs:
        submitted_reqs = load_applicant_requirements_map(
            cur, [applicant["applicant_id"]]
        ).get(applicant["applicant_id"], [])
    is_eligible, checks = check_eligibility(
        applicant, scholarship, required_reqs, submitted_reqs
    )
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
    eligible_rows = cur.fetchall()
    import sys
    _app_predict = getattr(sys.modules.get("app"), "predict_priority", None)
    if _app_predict is not None and _app_predict is not predict_priority:
        scores = [_app_predict(a, scholarship) for a in eligible_rows]
    else:
        scores = predict_priorities(eligible_rows, scholarship)
    scored = [(a["result_id"], score,
               program_standing(a["gwa"], scholarship),
               a["household_income"])
              for a, score in zip(eligible_rows, scores)]
    scored.sort(key=lambda x: (-x[1], -x[2], float(x[3]), x[0]))
    slots = scholarship["available_slots"] or 0
    for rank, (result_id, score, _gwa, _income) in enumerate(scored, 1):
        status = "SHORTLIST" if rank <= slots else "WAITLIST"
        cur.execute(
            "INSERT INTO ranking_results"
            " (result_id, priority_score, rank_position, status)"
            " VALUES (%s,%s,%s,%s)", (result_id, score, rank, status))
    return len(scored), min(len(scored), slots)


def renumber_ranking(cur, scholarship):
    """Re-number remaining ranking_results so rank_position has no gaps."""
    scholarship_id = scholarship["scholarship_id"]
    cur.execute(
        "SELECT rr.ranking_id FROM ranking_results rr"
        " JOIN screening_results sr ON sr.result_id = rr.result_id"
        " WHERE sr.scholarship_id=%s ORDER BY rr.rank_position, rr.ranking_id",
        (scholarship_id,))
    rows = cur.fetchall()
    slots = scholarship["available_slots"] or 0
    for rank, row in enumerate(rows, 1):
        status = "SHORTLIST" if rank <= slots else "WAITLIST"
        cur.execute(
            "UPDATE ranking_results SET rank_position=%s, status=%s"
            " WHERE ranking_id=%s",
            (rank, status, row["ranking_id"]))


def has_ranking(cur, scholarship_id):
    cur.execute(
        "SELECT 1 FROM ranking_results rr JOIN screening_results sr"
        " ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s LIMIT 1",
        (scholarship_id,))
    return cur.fetchone() is not None
