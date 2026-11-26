import datetime
import re

from flask import Blueprint, Response, abort, jsonify, request, session
from werkzeug.security import generate_password_hash

from backup_db import generate_sql_backup
from db import db, json_safe
from helpers import (current_org, current_role, json_body, record_audit,
                     require_roles)

admin_bp = Blueprint("admin", __name__)

ORG_ID_RE = re.compile(r"^[a-z0-9_-]{2,20}$")
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _clean_hex(value, label):
    val = str(value or "").strip()
    if not val:
        return None
    if not HEX_COLOR_RE.match(val):
        abort(400, f"{label} must be a 6-digit hex color like #002855")
    return val.upper()


def _clean_opacity(value, default, label):
    if value is None or value == "":
        return default
    try:
        v = float(value)
    except (TypeError, ValueError):
        abort(400, f"{label} must be a number between 0 and 1")
    if not 0.0 <= v <= 1.0:
        abort(400, f"{label} must be between 0 and 1")
    return round(v, 2)


def _clean_media(value, label):
    val = str(value or "").strip() or None
    if val and len(val) > 1_500_000:
        abort(400, f"{label} is too large (max ~1 MB)")
    return val


@admin_bp.route("/api/organizations", methods=["GET"])
def list_organizations():
    logged_in = "admin_id" in session
    with db() as (conn, cur):
        if logged_in:
            cur.execute(
                "SELECT organization_id, organization_name, is_active, logo_path,"
                " theme_primary_color, theme_accent_color, theme_bg_color,"
                " theme_bg_image, theme_bg_opacity, theme_surface_opacity"
                " FROM organizations ORDER BY organization_name")
        else:
            # Public login dropdown only needs identifiers & status — never send
            # multi-megabyte base64 logos or background images to unauthenticated clients.
            cur.execute(
                "SELECT organization_id, organization_name, is_active"
                " FROM organizations ORDER BY organization_name")
        rows = [json_safe(r) for r in cur.fetchall()]
    for r in rows:
        r["is_active"] = bool(r.get("is_active", 1))
    return jsonify(rows)


@admin_bp.route("/api/organizations", methods=["POST"])
def create_organization():
    require_roles("super_admin")
    data = json_body()
    org_id = str(data.get("organization_id") or "").strip().lower()
    org_name = str(data.get("organization_name") or "").strip()
    if not ORG_ID_RE.match(org_id):
        abort(400, "Organization ID must be 2 to 20 lowercase letters, "
                   "numbers, hyphens or underscores")
    if not org_name or len(org_name) > 150:
        abort(400, "Organization name is required (max 150 characters)")
    logo_path = _clean_media(data.get("logo_path"), "Logo")
    primary = _clean_hex(data.get("theme_primary_color"), "Primary color")
    accent = _clean_hex(data.get("theme_accent_color"), "Accent color")
    bg = _clean_hex(data.get("theme_bg_color"), "Background color")
    bg_img = _clean_media(data.get("theme_bg_image"), "Background image")
    bg_op = _clean_opacity(data.get("theme_bg_opacity"), 1.0, "Background opacity")
    surf_op = _clean_opacity(data.get("theme_surface_opacity"), 0.94, "Content block opacity")
    with db() as (conn, cur):
        cur.execute("SELECT 1 FROM organizations WHERE organization_id=%s",
                    (org_id,))
        if cur.fetchone() is not None:
            abort(409, "An organization with this ID already exists")
        cur.execute(
            "INSERT INTO organizations (organization_id, organization_name,"
            " logo_path, theme_primary_color, theme_accent_color, theme_bg_color,"
            " theme_bg_image, theme_bg_opacity, theme_surface_opacity)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (org_id, org_name, logo_path, primary, accent, bg, bg_img, bg_op, surf_op))
        record_audit(cur, "ORG_CREATE", "organization", org_id,
                     f"Created organization {org_name}", org_id=org_id)
        conn.commit()
    return jsonify({"organization_id": org_id}), 201


@admin_bp.route("/api/organizations/<org_id>", methods=["PUT"])
def update_organization(org_id):
    require_roles("super_admin", "owner")
    if current_role() == "owner" and org_id != current_org():
        abort(404, "Organization not found")
    data = json_body()
    org_name = str(data.get("organization_name") or "").strip()
    if not org_name or len(org_name) > 150:
        abort(400, "Organization name is required (max 150 characters)")
    logo_path = _clean_media(data.get("logo_path"), "Logo")
    primary = _clean_hex(data.get("theme_primary_color"), "Primary color")
    accent = _clean_hex(data.get("theme_accent_color"), "Accent color")
    bg = _clean_hex(data.get("theme_bg_color"), "Background color")
    bg_img = _clean_media(data.get("theme_bg_image"), "Background image")
    bg_op = _clean_opacity(data.get("theme_bg_opacity"), 1.0, "Background opacity")
    surf_op = _clean_opacity(data.get("theme_surface_opacity"), 0.94, "Content block opacity")
    with db() as (conn, cur):
        cur.execute("SELECT 1 FROM organizations WHERE organization_id=%s",
                    (org_id,))
        if cur.fetchone() is None:
            abort(404, "Organization not found")
        cur.execute(
            "UPDATE organizations SET organization_name=%s, logo_path=%s,"
            " theme_primary_color=%s, theme_accent_color=%s, theme_bg_color=%s,"
            " theme_bg_image=%s, theme_bg_opacity=%s, theme_surface_opacity=%s"
            " WHERE organization_id=%s",
            (org_name, logo_path, primary, accent, bg, bg_img, bg_op, surf_op, org_id))
        record_audit(cur, "ORG_UPDATE", "organization", org_id,
                     f"Updated branding/details for {org_id}", org_id=org_id)
        conn.commit()
    return jsonify({"organization_id": org_id})


@admin_bp.route("/api/organizations/<org_id>/deactivate", methods=["POST"])
def deactivate_organization(org_id):
    require_roles("super_admin")
    with db() as (conn, cur):
        cur.execute("SELECT organization_name FROM organizations WHERE organization_id=%s",
                    (org_id,))
        org = cur.fetchone()
        if org is None:
            abort(404, "Organization not found")
        cur.execute("UPDATE organizations SET is_active=0 WHERE organization_id=%s",
                    (org_id,))
        record_audit(cur, "ORG_DEACTIVATE", "organization", org_id,
                     f"Deactivated organization {org['organization_name']} ({org_id})",
                     org_id=org_id)
        conn.commit()
    return jsonify({"organization_id": org_id, "is_active": False})


@admin_bp.route("/api/organizations/<org_id>/reactivate", methods=["POST"])
def reactivate_organization(org_id):
    require_roles("super_admin")
    with db() as (conn, cur):
        cur.execute("SELECT organization_name FROM organizations WHERE organization_id=%s",
                    (org_id,))
        org = cur.fetchone()
        if org is None:
            abort(404, "Organization not found")
        cur.execute("UPDATE organizations SET is_active=1 WHERE organization_id=%s",
                    (org_id,))
        record_audit(cur, "ORG_REACTIVATE", "organization", org_id,
                     f"Reactivated organization {org['organization_name']} ({org_id})",
                     org_id=org_id)
        conn.commit()
    return jsonify({"organization_id": org_id, "is_active": True})


def _load_managed_admin(cur, admin_id):
    cur.execute(
        "SELECT admin_id, organization_id, full_name, email, role, is_active,"
        " last_login, failed_attempts, locked_until, must_change_pw, date_added"
        " FROM administrators WHERE admin_id=%s", (admin_id,))
    row = cur.fetchone()
    if row is None:
        abort(404, "Administrator not found")
    if current_role() != "super_admin" and row["organization_id"] != current_org():
        abort(404, "Administrator not found")
    return row


def _guard_target_hierarchy(target):
    """Prevent an Organization Owner from editing, resetting, or deactivating
    any Global Super Admin account."""
    if target["role"] == "super_admin" and current_role() != "super_admin":
        abort(403, "Only a Super Admin can modify a Super Admin account")


def _active_super_admin_count(cur):
    cur.execute(
        "SELECT COUNT(*) AS n FROM administrators"
        " WHERE role='super_admin' AND is_active=1"
    )
    return cur.fetchone()["n"]


def _active_owner_count(cur, org_id):
    cur.execute(
        "SELECT COUNT(*) AS n FROM administrators"
        " WHERE organization_id=%s AND role='owner' AND is_active=1",
        (org_id,))
    return cur.fetchone()["n"]


@admin_bp.route("/api/admins", methods=["GET"])
def list_admins():
    require_roles("super_admin", "owner")
    org = request.args.get("organization_id")
    cols = (
        "admin_id, organization_id, full_name, email, role, is_active,"
        " last_login, failed_attempts, locked_until, must_change_pw, date_added,"
        " (locked_until IS NOT NULL AND locked_until > CURRENT_TIMESTAMP) AS is_locked"
    )
    with db() as (conn, cur):
        if current_role() == "super_admin":
            if org:
                cur.execute(
                    f"SELECT {cols} FROM administrators WHERE organization_id=%s"
                    " ORDER BY admin_id", (org,))
            else:
                cur.execute(
                    f"SELECT {cols} FROM administrators ORDER BY organization_id, admin_id")
        else:
            cur.execute(
                f"SELECT {cols} FROM administrators WHERE organization_id=%s"
                " ORDER BY admin_id", (current_org(),))
        rows = [json_safe(r) for r in cur.fetchall()]
    for r in rows:
        r["is_active"] = bool(r["is_active"])
        r["is_locked"] = bool(r.get("is_locked"))
        r["must_change_pw"] = bool(r["must_change_pw"])
    return jsonify(rows)


@admin_bp.route("/api/admins", methods=["POST"])
def create_admin():
    require_roles("super_admin", "owner")
    data = json_body()
    org_id = str(data.get("organization_id") or current_org()).strip()
    if current_role() != "super_admin" and org_id != current_org():
        abort(403, "You can only create administrators for your own organization")
    full_name = str(data.get("full_name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    role = str(data.get("role") or "admin").strip()
    if not full_name or len(full_name) > 150:
        abort(400, "Full name is required (max 150 characters)")
    if not email or "@" not in email or len(email) > 150:
        abort(400, "A valid email address is required")
    if len(password) < 8:
        abort(400, "Password must be at least 8 characters")
    allowed_roles = ("owner", "admin", "super_admin") if current_role() == "super_admin" else ("owner", "admin")
    if role not in allowed_roles:
        abort(400, "Invalid role")
    with db() as (conn, cur):
        cur.execute("SELECT 1 FROM organizations WHERE organization_id=%s", (org_id,))
        if cur.fetchone() is None:
            abort(404, "Organization not found")
        cur.execute("SELECT 1 FROM administrators WHERE email=%s", (email,))
        if cur.fetchone() is not None:
            abort(409, "An administrator with this email already exists")
        cur.execute(
            "INSERT INTO administrators"
            " (organization_id, full_name, email, password_hash, role, must_change_pw)"
            " VALUES (%s,%s,%s,%s,%s,1)",
            (org_id, full_name, email,
             generate_password_hash(password, method="pbkdf2:sha256"), role))
        new_id = cur.lastrowid
        record_audit(cur, "ADMIN_CREATE", "administrator", new_id,
                     f"Created {role} account {email} in {org_id}")
        conn.commit()
    return jsonify({"admin_id": new_id}), 201


@admin_bp.route("/api/admins/<int:admin_id>", methods=["PUT"])
def update_admin(admin_id):
    require_roles("super_admin", "owner")
    data = json_body()
    with db() as (conn, cur):
        target = _load_managed_admin(cur, admin_id)
        _guard_target_hierarchy(target)
        full_name = str(data.get("full_name") or target["full_name"]).strip()
        email = str(data.get("email") or target["email"]).strip().lower()
        new_role = str(data.get("role") or target["role"]).strip()
        if not full_name or len(full_name) > 150:
            abort(400, "Full name is required (max 150 characters)")
        if not email or "@" not in email or len(email) > 150:
            abort(400, "A valid email address is required")
        allowed_roles = ("owner", "admin", "super_admin") if current_role() == "super_admin" else ("owner", "admin")
        if new_role not in allowed_roles:
            abort(400, "Invalid role")
        if admin_id == session["admin_id"] and new_role != target["role"]:
            abort(400, "You cannot change your own role")
        if target["role"] == "super_admin" and new_role != "super_admin" and target["is_active"]:
            if _active_super_admin_count(cur) <= 1:
                abort(400, "Cannot demote the last active Super Admin")
        if target["role"] == "owner" and new_role != "owner" and target["is_active"]:
            if _active_owner_count(cur, target["organization_id"]) <= 1:
                abort(400, "Cannot demote the last active owner of an organization")
        cur.execute("SELECT 1 FROM administrators WHERE email=%s AND admin_id<>%s",
                    (email, admin_id))
        if cur.fetchone() is not None:
            abort(409, "Another administrator already uses this email")
        cur.execute(
            "UPDATE administrators SET full_name=%s, email=%s, role=%s"
            " WHERE admin_id=%s", (full_name, email, new_role, admin_id))
        record_audit(cur, "ADMIN_UPDATE", "administrator", admin_id,
                     f"Updated {email} (role: {new_role})")
        conn.commit()
    return jsonify({"admin_id": admin_id})


@admin_bp.route("/api/admins/<int:admin_id>/reset-password", methods=["POST"])
def reset_admin_password(admin_id):
    require_roles("super_admin", "owner")
    data = json_body()
    new_pw = str(data.get("new_password") or "")
    if len(new_pw) < 8:
        abort(400, "New password must be at least 8 characters")
    with db() as (conn, cur):
        target = _load_managed_admin(cur, admin_id)
        _guard_target_hierarchy(target)
        cur.execute(
            "UPDATE administrators SET password_hash=%s, must_change_pw=1,"
            " failed_attempts=0, locked_until=NULL WHERE admin_id=%s",
            (generate_password_hash(new_pw, method="pbkdf2:sha256"), admin_id))
        record_audit(cur, "ADMIN_RESET_PW", "administrator", admin_id,
                     f"Reset password for {target['email']}")
        conn.commit()
    return jsonify({"ok": True})


@admin_bp.route("/api/admins/<int:admin_id>/deactivate", methods=["POST"])
def deactivate_admin(admin_id):
    require_roles("super_admin", "owner")
    if admin_id == session["admin_id"]:
        abort(400, "You cannot deactivate your own account")
    with db() as (conn, cur):
        target = _load_managed_admin(cur, admin_id)
        _guard_target_hierarchy(target)
        if target["role"] == "super_admin" and target["is_active"]:
            if _active_super_admin_count(cur) <= 1:
                abort(400, "Cannot deactivate the last active Super Admin")
        if target["role"] == "owner" and target["is_active"]:
            if _active_owner_count(cur, target["organization_id"]) <= 1:
                abort(400, "Cannot deactivate the last active owner of an organization")
        cur.execute("UPDATE administrators SET is_active=0 WHERE admin_id=%s",
                    (admin_id,))
        record_audit(cur, "ADMIN_DEACTIVATE", "administrator", admin_id,
                     f"Deactivated {target['email']}")
        conn.commit()
    return jsonify({"ok": True})


@admin_bp.route("/api/admins/<int:admin_id>/reactivate", methods=["POST"])
def reactivate_admin(admin_id):
    require_roles("super_admin", "owner")
    with db() as (conn, cur):
        target = _load_managed_admin(cur, admin_id)
        _guard_target_hierarchy(target)
        cur.execute(
            "UPDATE administrators SET is_active=1, failed_attempts=0, locked_until=NULL"
            " WHERE admin_id=%s", (admin_id,))
        record_audit(cur, "ADMIN_REACTIVATE", "administrator", admin_id,
                     f"Reactivated/unlocked {target['email']}")
        conn.commit()
    return jsonify({"ok": True})


@admin_bp.route("/api/audit-logs", methods=["GET"])
def get_audit_logs():
    require_roles("super_admin", "owner")
    org = request.args.get("organization_id")
    limit = min(max(int(request.args.get("limit", 200)), 1), 500)
    with db() as (conn, cur):
        base_sql = (
            "SELECT al.log_id, al.organization_id, al.admin_id,"
            " a.full_name AS admin_name, a.email AS admin_email,"
            " al.action, al.target_type, al.target_id, al.details, al.created_at"
            " FROM audit_logs al"
            " LEFT JOIN administrators a ON a.admin_id = al.admin_id"
        )
        if current_role() == "super_admin":
            if org:
                cur.execute(base_sql + " WHERE al.organization_id=%s"
                            " ORDER BY al.log_id DESC LIMIT %s", (org, limit))
            else:
                cur.execute(base_sql + " ORDER BY al.log_id DESC LIMIT %s",
                            (limit,))
        else:
            cur.execute(base_sql + " WHERE al.organization_id=%s"
                        " ORDER BY al.log_id DESC LIMIT %s",
                        (current_org(), limit))
        return jsonify([json_safe(r) for r in cur.fetchall()])


@admin_bp.route("/api/admin/backup.sql", methods=["GET"])
def download_sql_backup():
    require_roles("super_admin")
    sql_text = generate_sql_backup(record_event=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return Response(
        sql_text,
        mimetype="application/sql",
        headers={
            "Content-Disposition": f"attachment; filename=edumatch_backup_{stamp}.sql"
        },
    )
