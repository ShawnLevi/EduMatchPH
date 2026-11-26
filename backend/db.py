import datetime
import os
from contextlib import contextmanager
from decimal import Decimal

import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),  # XAMPP default
        database=os.environ.get("DB_NAME", "edumatch_db"),
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


_SCHEMA_ENSURED = False


def ensure_schema():
    """Idempotently add new governance columns on existing local databases so
    switching branches or pulling updates never crashes without re-importing SQL."""
    global _SCHEMA_ENSURED
    if _SCHEMA_ENSURED:
        return
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SHOW COLUMNS FROM organizations LIKE 'is_active'")
            if cur.fetchone() is None:
                cur.execute(
                    "ALTER TABLE organizations"
                    " ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1"
                    " AFTER organization_name"
                )
            cur.execute("SHOW COLUMNS FROM administrators LIKE 'locked_until'")
            if cur.fetchone() is None:
                cur.execute(
                    "ALTER TABLE administrators"
                    " ADD COLUMN locked_until TIMESTAMP NULL"
                    " AFTER failed_attempts"
                )
            # Ensure seeded starter organizations each have an active Owner
            for org_id, seed_email in (
                ("uclm", "alicia.ramos@uclm.edu.ph"),
                ("dost", "marco.villanueva@dost.gov.ph"),
            ):
                cur.execute(
                    "SELECT COUNT(*) AS n FROM administrators"
                    " WHERE organization_id=%s AND role='owner' AND is_active=1",
                    (org_id,),
                )
                if cur.fetchone()["n"] == 0:
                    cur.execute(
                        "UPDATE administrators SET role='owner'"
                        " WHERE email=%s AND organization_id=%s AND role='admin'",
                        (seed_email, org_id),
                    )
            cur.execute(
                "UPDATE grade_scales"
                " SET notes='For partner institutions using a 5.00-highest cumulative scale where 3.00 is passing.'"
                " WHERE scale_id='SCALE_5_BEST' AND notes LIKE 'EXAMPLE%'"
            )
            conn.commit()
            _SCHEMA_ENSURED = True
        finally:
            cur.close()
            conn.close()
    except Exception:
        pass


@contextmanager
def db():
    """with db() as (conn, cur): ...  Always closes, even after an error.
    If an error happens before conn.commit(), nothing is saved."""
    ensure_schema()
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        yield conn, cur
    finally:
        cur.close()
        conn.close()


def json_safe(row):
    """MySQL returns DECIMAL columns as Decimal and dates as date objects.
    Convert them so every API response sends plain numbers and text."""
    out = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            out[key] = float(value)
        elif isinstance(value, (datetime.date, datetime.datetime)):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out
