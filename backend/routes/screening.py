from flask import Blueprint, abort, jsonify, request

from db import db, json_safe
from helpers import (has_ranking, load_applicant_requirements_map,
                     load_program_requirements, load_scholarship, record_audit,
                     screen_one, write_ranking)
from ranking import explain_priority

screening_bp = Blueprint("screening", __name__)


@screening_bp.route("/api/scholarships/<int:scholarship_id>/screen",
                    methods=["POST"])
def screen_scholarship(scholarship_id):
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        if scholarship["status"] == "Closed":
            abort(400, "This program is closed. Reopen it to run screening")
        cur.execute("DELETE FROM screening_results WHERE scholarship_id=%s",
                    (scholarship_id,))
        cur.execute("SELECT * FROM applicants WHERE scholarship_id=%s",
                    (scholarship_id,))
        applicants = cur.fetchall()
        req_labels = load_program_requirements(cur, scholarship_id)
        submitted_map = (
            load_applicant_requirements_map(
                cur, [a["applicant_id"] for a in applicants]
            )
            if req_labels and applicants else {}
        )
        results = []
        for a in applicants:
            is_eligible = screen_one(
                cur, a, scholarship, req_labels,
                submitted_map.get(a["applicant_id"], []),
            )
            results.append({"applicant_id": a["applicant_id"],
                            "eligible": bool(is_eligible)})
        cur.execute("UPDATE scholarship_programs SET status='Screening'"
                    " WHERE scholarship_id=%s", (scholarship_id,))
        record_audit(cur, "SCREENING_RUN", "scholarship", scholarship_id,
                     f"Screened {len(results)} applicants")
        conn.commit()
        return jsonify(results)


@screening_bp.route("/api/scholarships/<int:scholarship_id>/rank",
                    methods=["POST"])
def rank_scholarship(scholarship_id):
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        if scholarship["status"] == "Closed":
            abort(400, "This program is closed. Reopen it to run ranking")
        cur.execute("SELECT COUNT(*) AS n FROM screening_results"
                    " WHERE scholarship_id=%s", (scholarship_id,))
        if cur.fetchone()["n"] == 0:
            abort(400, "Run screening before ranking")
        scored_count, shortlisted = write_ranking(cur, scholarship)
        cur.execute("UPDATE scholarship_programs SET status='Ranking'"
                    " WHERE scholarship_id=%s", (scholarship_id,))
        record_audit(cur, "RANKING_RUN", "scholarship", scholarship_id,
                     f"Ranked {scored_count} eligible applicants ({shortlisted} shortlisted)")
        conn.commit()
        return jsonify({"ranked_count": scored_count,
                        "shortlisted": shortlisted,
                        "waitlisted": scored_count - shortlisted})


@screening_bp.route("/api/scholarships/<int:scholarship_id>/shortlist",
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


@screening_bp.route("/api/scholarships/<int:scholarship_id>/applicants/"
                    "<int:applicant_id>/screen", methods=["POST"])
def screen_applicant(scholarship_id, applicant_id):
    data = request.get_json(silent=True) or {}
    want_rank = bool(data.get("rank"))
    with db() as (conn, cur):
        scholarship = load_scholarship(cur, scholarship_id)
        if scholarship["status"] == "Closed":
            abort(400, "This program is closed. Reopen it to run screening")
        cur.execute("SELECT * FROM applicants WHERE applicant_id=%s"
                    " AND scholarship_id=%s", (applicant_id, scholarship_id))
        applicant = cur.fetchone()
        if applicant is None:
            abort(404, "Applicant not found")
        ranked_before = has_ranking(cur, scholarship_id)
        if want_rank and not ranked_before:
            abort(400, "This program has not been ranked yet. Run ranking "
                       "for the whole program first")
        cur.execute("DELETE FROM screening_results WHERE applicant_id=%s",
                    (applicant_id,))
        is_eligible = bool(screen_one(cur, applicant, scholarship))
        out = {"applicant_id": applicant_id, "eligible": is_eligible,
               "ranked": False}
        if want_rank:
            write_ranking(cur, scholarship)
            cur.execute("UPDATE scholarship_programs SET status='Ranking'"
                        " WHERE scholarship_id=%s", (scholarship_id,))
            if is_eligible:
                cur.execute(
                    "SELECT rr.priority_score, rr.rank_position, rr.status"
                    " FROM ranking_results rr JOIN screening_results sr"
                    " ON sr.result_id = rr.result_id"
                    " WHERE sr.applicant_id=%s", (applicant_id,))
                row = cur.fetchone()
                out.update(ranked=True,
                           priority_score=float(row["priority_score"]),
                           rank_position=row["rank_position"],
                           status=row["status"])
        elif scholarship["status"] == "Open":
            cur.execute("UPDATE scholarship_programs SET status='Screening'"
                        " WHERE scholarship_id=%s", (scholarship_id,))
        conn.commit()
        return jsonify(out)


@screening_bp.route("/api/scholarships/<int:scholarship_id>/applicants/"
                    "<int:applicant_id>/explanation", methods=["GET"])
def explain_applicant(scholarship_id, applicant_id):
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


@screening_bp.route("/api/scholarships/<int:scholarship_id>/screening",
                    methods=["GET"])
def get_screening_details(scholarship_id):
    with db() as (conn, cur):
        load_scholarship(cur, scholarship_id)
        cur.execute(
            "SELECT sr.result_id, a.applicant_id, a.full_name, sr.eligible,"
            " rs.criterion_name, rs.applicant_value, rs.threshold_value, rs.met"
            " FROM screening_results sr"
            " JOIN applicants a ON a.applicant_id = sr.applicant_id"
            " LEFT JOIN screening_reasons rs ON rs.result_id = sr.result_id"
            " WHERE sr.scholarship_id=%s"
            " ORDER BY a.applicant_id, rs.reason_id",
            (scholarship_id,))
        by_result = {}
        for r in cur.fetchall():
            entry = by_result.setdefault(r["result_id"], {
                "applicant_id": r["applicant_id"],
                "full_name": r["full_name"],
                "eligible": bool(r["eligible"]),
                "reasons": [],
            })
            if r["criterion_name"] is not None:
                entry["reasons"].append({
                    "criterion_name": r["criterion_name"],
                    "applicant_value": r["applicant_value"],
                    "threshold_value": r["threshold_value"],
                    "met": bool(r["met"]),
                })
        return jsonify(list(by_result.values()))
