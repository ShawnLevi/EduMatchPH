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


@contextmanager
def db():
    """with db() as (conn, cur): ...  Always closes, even after an error.
    If an error happens before conn.commit(), nothing is saved."""
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
