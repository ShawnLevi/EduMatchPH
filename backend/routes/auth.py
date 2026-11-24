from flask import Blueprint, abort, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import db
from helpers import json_body, load_scales, record_audit
from reference import (COURSES, FIELDS, LOCALITIES, LOCATION_REQ_CHOICES,
                       STATUSES)

auth_bp = Blueprint("auth", __name__)

MAX_FAILED_LOGINS = 5


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    org = str(data.get("organization_id") or "").strip()
    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "")
    if not (org and email and password):
        abort(400, "Enter your organization, email and password")
    with db() as (conn, cur):
        cur.execute(
            "SELECT * FROM administrators"
            " WHERE email=%s AND organization_id=%s", (email, org))
        admin = cur.fetchone()
        if admin is None:
            abort(401, "Wrong email or password for this organization")
        if not admin["is_active"]:
            record_audit(cur, "LOGIN_BLOCKED", "administrator",
                         admin["admin_id"], f"Blocked login for {email}",
                         org_id=admin["organization_id"],
                         admin_id=admin["admin_id"])
            conn.commit()
            abort(403, "This account is deactivated or locked. Contact your "
                       "organization owner or system administrator")
        if not check_password_hash(admin["password_hash"], password):
            attempts = (admin["failed_attempts"] or 0) + 1
            locked = attempts >= MAX_FAILED_LOGINS
            cur.execute(
                "UPDATE administrators SET failed_attempts=%s, is_active=%s"
                " WHERE admin_id=%s",
                (attempts, 0 if locked else 1, admin["admin_id"]))
            record_audit(cur, "ACCOUNT_LOCKED" if locked else "LOGIN_FAILED",
                         "administrator", admin["admin_id"],
                         f"Failed attempt {attempts} for {email}",
                         org_id=admin["organization_id"],
                         admin_id=admin["admin_id"])
            conn.commit()
            if locked:
                abort(403, "Account locked after 5 failed login attempts. "
                           "Contact your administrator")
            abort(401, "Wrong email or password for this organization")
        cur.execute(
            "UPDATE administrators SET failed_attempts=0,"
            " last_login=CURRENT_TIMESTAMP WHERE admin_id=%s",
            (admin["admin_id"],))
        record_audit(cur, "LOGIN_SUCCESS", "administrator", admin["admin_id"],
                     f"{email} logged in",
                     org_id=admin["organization_id"],
                     admin_id=admin["admin_id"])
        conn.commit()
    session.clear()
    session.permanent = True
    session["admin_id"] = admin["admin_id"]
    session["organization_id"] = admin["organization_id"]
    session["full_name"] = admin["full_name"]
    session["role"] = admin["role"]
    return jsonify({"admin_id": admin["admin_id"],
                    "full_name": admin["full_name"],
                    "organization_id": admin["organization_id"],
                    "role": admin["role"],
                    "must_change_pw": bool(admin["must_change_pw"])})


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    if "admin_id" in session:
        with db() as (conn, cur):
            record_audit(cur, "LOGOUT", "administrator", session["admin_id"],
                         "Administrator logged out")
            conn.commit()
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/api/me", methods=["GET"])
def me():
    if "admin_id" not in session:
        abort(401, "Not logged in")
    with db() as (conn, cur):
        cur.execute(
            "SELECT admin_id, full_name, organization_id, role, is_active,"
            " must_change_pw FROM administrators WHERE admin_id=%s",
            (session["admin_id"],))
        admin = cur.fetchone()
    if admin is None or not admin["is_active"]:
        session.clear()
        abort(401, "Not logged in")
    return jsonify({"admin_id": admin["admin_id"],
                    "full_name": admin["full_name"],
                    "organization_id": admin["organization_id"],
                    "role": admin["role"],
                    "must_change_pw": bool(admin["must_change_pw"])})


@auth_bp.route("/api/change-password", methods=["POST"])
def change_password():
    data = json_body()
    current_pw = str(data.get("current_password") or "")
    new_pw = str(data.get("new_password") or "")
    if not current_pw or not new_pw:
        abort(400, "Enter your current password and a new password")
    if len(new_pw) < 8:
        abort(400, "New password must be at least 8 characters")
    if current_pw == new_pw:
        abort(400, "New password must be different from your current password")
    with db() as (conn, cur):
        cur.execute("SELECT password_hash FROM administrators WHERE admin_id=%s",
                    (session["admin_id"],))
        row = cur.fetchone()
        if row is None or not check_password_hash(row["password_hash"], current_pw):
            abort(401, "Current password is incorrect")
        cur.execute(
            "UPDATE administrators SET password_hash=%s, must_change_pw=0"
            " WHERE admin_id=%s",
            (generate_password_hash(new_pw, method="pbkdf2:sha256"),
             session["admin_id"]))
        record_audit(cur, "PASSWORD_CHANGE", "administrator",
                     session["admin_id"], "Changed own password")
        conn.commit()
    return jsonify({"ok": True})


@auth_bp.route("/api/meta", methods=["GET"])
def meta():
    """Lists for the form dropdowns, so the frontend never hardcodes them."""
    return jsonify({"courses": COURSES, "localities": LOCALITIES,
                    "location_req_choices": LOCATION_REQ_CHOICES,
                    "fields": FIELDS, "statuses": STATUSES,
                    "grade_scales": load_scales()})
