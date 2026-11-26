from flask import Blueprint, abort, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import db, json_safe
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
    if not (email and password):
        abort(400, "Enter your email and password")
    with db() as (conn, cur):
        if not org or org == "__all__":
            cur.execute(
                "SELECT *, (locked_until IS NOT NULL AND locked_until > CURRENT_TIMESTAMP) AS currently_locked"
                " FROM administrators"
                " WHERE email=%s AND role='super_admin'", (email,))
        else:
            cur.execute(
                "SELECT *, (locked_until IS NOT NULL AND locked_until > CURRENT_TIMESTAMP) AS currently_locked"
                " FROM administrators"
                " WHERE email=%s AND (organization_id=%s OR role='super_admin')",
                (email, org))
        admin = cur.fetchone()
        if admin is None:
            abort(401, "Wrong email or password for this organization")
        if not admin["is_active"]:
            record_audit(cur, "LOGIN_BLOCKED", "administrator",
                         admin["admin_id"], f"Blocked login for {email} (account inactive)",
                         org_id=admin["organization_id"],
                         admin_id=admin["admin_id"])
            conn.commit()
            abort(403, "This account is deactivated. Contact your "
                       "organization owner or system administrator")
        if admin["currently_locked"]:
            record_audit(cur, "LOGIN_BLOCKED", "administrator",
                         admin["admin_id"], f"Blocked login during cooldown for {email}",
                         org_id=admin["organization_id"],
                         admin_id=admin["admin_id"])
            conn.commit()
            abort(403, "Account temporarily locked after 5 failed login attempts. "
                       "Try again in a few minutes or contact your administrator")
        cur.execute(
            "SELECT organization_id, organization_name, is_active, logo_path,"
            " theme_primary_color, theme_accent_color, theme_bg_color,"
            " theme_bg_image, theme_bg_opacity, theme_surface_opacity"
            " FROM organizations WHERE organization_id=%s",
            (admin["organization_id"],))
        org_row = cur.fetchone()
        if admin["role"] != "super_admin" and org_row is not None and not org_row["is_active"]:
            record_audit(cur, "LOGIN_BLOCKED", "organization",
                         admin["organization_id"],
                         f"Blocked login for {email} (organization deactivated)",
                         org_id=admin["organization_id"],
                         admin_id=admin["admin_id"])
            conn.commit()
            abort(403, "This organization's account is currently deactivated. "
                       "Contact the system administrator")
        if not check_password_hash(admin["password_hash"], password):
            prior_attempts = 0 if (admin.get("locked_until") is not None and not admin["currently_locked"]) else (admin["failed_attempts"] or 0)
            attempts = prior_attempts + 1
            locked = attempts >= MAX_FAILED_LOGINS
            cooldown_mins = 5 if admin["role"] == "super_admin" else 15
            if locked:
                cur.execute(
                    "UPDATE administrators SET failed_attempts=%s,"
                    " locked_until=TIMESTAMPADD(MINUTE, %s, CURRENT_TIMESTAMP)"
                    " WHERE admin_id=%s",
                    (attempts, cooldown_mins, admin["admin_id"]))
            else:
                cur.execute(
                    "UPDATE administrators SET failed_attempts=%s, locked_until=NULL"
                    " WHERE admin_id=%s",
                    (attempts, admin["admin_id"]))
            record_audit(cur, "ACCOUNT_LOCKED" if locked else "LOGIN_FAILED",
                         "administrator", admin["admin_id"],
                         f"Failed attempt {attempts} for {email}",
                         org_id=admin["organization_id"],
                         admin_id=admin["admin_id"])
            conn.commit()
            if locked:
                abort(403, f"Account temporarily locked for {cooldown_mins} minutes "
                           "after 5 failed login attempts")
            abort(401, "Wrong email or password for this organization")
        cur.execute(
            "UPDATE administrators SET failed_attempts=0, locked_until=NULL,"
            " last_login=CURRENT_TIMESTAMP WHERE admin_id=%s",
            (admin["admin_id"],))
        record_audit(cur, "LOGIN_SUCCESS", "administrator", admin["admin_id"],
                     f"{email} logged in",
                     org_id=admin["organization_id"],
                     admin_id=admin["admin_id"])
        conn.commit()
    if org_row is not None:
        org_row = json_safe(org_row)
        org_row["is_active"] = bool(org_row.get("is_active", 1))
    session.clear()
    session.permanent = True
    session["admin_id"] = admin["admin_id"]
    session["organization_id"] = admin["organization_id"]
    session["full_name"] = admin["full_name"]
    session["role"] = admin["role"]
    return jsonify({"admin_id": admin["admin_id"],
                    "full_name": admin["full_name"],
                    "email": admin["email"],
                    "organization_id": admin["organization_id"],
                    "role": admin["role"],
                    "must_change_pw": bool(admin["must_change_pw"]),
                    "avatar_url": admin.get("avatar_url"),
                    "organization": org_row})


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
            "SELECT admin_id, full_name, email, organization_id, role,"
            " is_active, must_change_pw, avatar_url,"
            " (locked_until IS NOT NULL AND locked_until > CURRENT_TIMESTAMP) AS currently_locked"
            " FROM administrators WHERE admin_id=%s",
            (session["admin_id"],))
        admin = cur.fetchone()
        if admin is None or not admin["is_active"] or admin["currently_locked"]:
            session.clear()
            abort(401, "Not logged in")
        cur.execute(
            "SELECT organization_id, organization_name, is_active, logo_path,"
            " theme_primary_color, theme_accent_color, theme_bg_color,"
            " theme_bg_image, theme_bg_opacity, theme_surface_opacity"
            " FROM organizations WHERE organization_id=%s",
            (admin["organization_id"],))
        org_row = cur.fetchone()
        if admin["role"] != "super_admin" and org_row is not None and not org_row["is_active"]:
            session.clear()
            abort(403, "This organization's account is currently deactivated")
    session["role"] = admin["role"]
    session["organization_id"] = admin["organization_id"]
    session["full_name"] = admin["full_name"]
    if org_row is not None:
        org_row = json_safe(org_row)
        org_row["is_active"] = bool(org_row.get("is_active", 1))
    return jsonify({"admin_id": admin["admin_id"],
                    "full_name": admin["full_name"],
                    "email": admin["email"],
                    "organization_id": admin["organization_id"],
                    "role": admin["role"],
                    "must_change_pw": bool(admin["must_change_pw"]),
                    "avatar_url": admin.get("avatar_url"),
                    "organization": org_row})


@auth_bp.route("/api/me/profile", methods=["PUT"])
def update_profile():
    data = json_body()
    full_name = str(data.get("full_name") or "").strip()
    if not full_name or len(full_name) > 150:
        abort(400, "Full name is required (max 150 characters)")
    avatar = data.get("avatar_url")
    if avatar is not None:
        avatar = str(avatar).strip() or None
        if avatar and len(avatar) > 1_500_000:
            abort(400, "Profile image is too large (max ~1 MB)")
    with db() as (conn, cur):
        if "avatar_url" in data:
            cur.execute(
                "UPDATE administrators SET full_name=%s, avatar_url=%s"
                " WHERE admin_id=%s",
                (full_name, avatar, session["admin_id"]))
        else:
            cur.execute(
                "UPDATE administrators SET full_name=%s WHERE admin_id=%s",
                (full_name, session["admin_id"]))
        record_audit(cur, "PROFILE_UPDATE", "administrator",
                     session["admin_id"], f"Updated profile for {full_name}")
        conn.commit()
    session["full_name"] = full_name
    return jsonify({"full_name": full_name, "avatar_url": avatar})


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
