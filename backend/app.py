import datetime
import os

from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from db import db
from ranking import predict_priority  # noqa: F401 - exposed on app for test_api.py
from routes.admin import admin_bp
from routes.applicants import applicants_bp
from routes.auth import auth_bp
from routes.exports import exports_bp
from routes.programs import programs_bp
from routes.screening import screening_bp

app = Flask(__name__)
# Set EDUMATCH_SECRET in the environment. It signs the login cookie.
app.secret_key = os.environ.get("EDUMATCH_SECRET", "dev-only-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.permanent_session_lifetime = datetime.timedelta(hours=2)
# The frontend runs on another port (for example 5500) on localhost, so allow
# localhost / 127.0.0.1 on any port, WITH cookies (the login).
CORS(app, supports_credentials=True,
     origins=r"http://(localhost|127\.0\.0\.1)(:\d+)?")


@app.errorhandler(HTTPException)
def http_error(e):
    return jsonify({"error": e.description}), e.code


@app.errorhandler(Exception)
def server_error(e):
    app.logger.exception("Unexpected error")
    return jsonify({"error": "EduMatch PH could not complete this request. "
                             "Please try again. If the problem continues, "
                             "contact your system administrator."}), 500


PUBLIC_ENDPOINTS = {
    "auth.login",
    "auth.logout",
    "auth.me",
    "auth.meta",
    "admin.list_organizations",
}


@app.before_request
def require_login():
    if request.method == "OPTIONS" or request.endpoint in (None, "static"):
        return None
    if request.endpoint in PUBLIC_ENDPOINTS:
        return None
    if "admin_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    # Live session re-verification: immediately enforce account deactivation,
    # organization deactivation, temporary lockouts, role changes, and
    # mandatory password updates instead of trusting a 2-hour cookie blindly.
    with db() as (conn, cur):
        cur.execute(
            "SELECT a.admin_id, a.organization_id, a.full_name, a.role,"
            " a.is_active, a.must_change_pw,"
            " (a.locked_until IS NOT NULL AND a.locked_until > CURRENT_TIMESTAMP) AS is_locked,"
            " COALESCE(o.is_active, 1) AS org_is_active"
            " FROM administrators a"
            " LEFT JOIN organizations o ON o.organization_id = a.organization_id"
            " WHERE a.admin_id=%s",
            (session["admin_id"],),
        )
        live = cur.fetchone()
    if live is None or not live["is_active"] or live["is_locked"]:
        session.clear()
        return jsonify({"error": "Your session is no longer active. Please log in again"}), 401
    if live["role"] != "super_admin" and not live["org_is_active"]:
        session.clear()
        return jsonify({"error": "This organization's account is currently deactivated"}), 403

    session["role"] = live["role"]
    session["organization_id"] = live["organization_id"]
    session["full_name"] = live["full_name"]

    if live["must_change_pw"] and request.blueprint in (
        "programs", "applicants", "screening", "exports"
    ):
        return jsonify({
            "error": "Password change required. Please set a new password before continuing"
        }), 403
    return None


app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(programs_bp)
app.register_blueprint(applicants_bp)
app.register_blueprint(screening_bp)
app.register_blueprint(exports_bp)


if __name__ == "__main__":
    app.run(debug=os.environ.get("EDUMATCH_DEBUG") == "1", port=5000)
