"""
EduMatch PH — Portable SQL Database Backup Tool.
Works without external mysqldump binaries by reading live DDL and row data
directly through the Python MySQL connector in foreign-key-safe order.

Usage (CLI):
    python backup_db.py [optional_output_path.sql]
"""
import datetime
import decimal
import os
import sys

from db import db

# Topological table order respecting foreign-key dependencies
BACKUP_TABLES = [
    "organizations",
    "grade_scales",
    "requirement_types",
    "administrators",
    "scholarship_programs",
    "program_requirements",
    "applicants",
    "applicant_requirements",
    "screening_results",
    "screening_reasons",
    "ranking_results",
    "audit_logs",
]


def _sql_literal(val):
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float, decimal.Decimal)):
        return str(val)
    if isinstance(val, (datetime.datetime, datetime.date)):
        s = val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(val, datetime.datetime) else val.isoformat()
        return f"'{s}'"
    if isinstance(val, (bytes, bytearray)):
        return "0x" + bytes(val).hex()
    s = (
        str(val)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\x00", "")
    )
    return f"'{s}'"


def generate_sql_backup(record_event=False):
    """Return a complete, restorable UTF-8 SQL dump string of edumatch_db."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "-- ============================================================",
        f"-- EduMatch PH Database Backup — Generated {now_str}",
        "-- ============================================================",
        "SET NAMES utf8mb4;",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "",
    ]
    with db() as (conn, cur):
        if record_event:
            from helpers import record_audit
            record_audit(cur, "DB_BACKUP_EXPORT", "database", "edumatch_db",
                         "Exported full SQL database backup")
            conn.commit()

        cur.execute("SHOW TABLES")
        existing = {list(r.values())[0] for r in cur.fetchall()}
        ordered = [t for t in BACKUP_TABLES if t in existing] + sorted(
            existing - set(BACKUP_TABLES)
        )

        for tbl in ordered:
            lines.append(f"-- Table: `{tbl}`")
            lines.append(f"DROP TABLE IF EXISTS `{tbl}`;")
            cur.execute(f"SHOW CREATE TABLE `{tbl}`")
            ddl_row = cur.fetchone()
            create_sql = ddl_row.get("Create Table") or list(ddl_row.values())[1]
            lines.append(create_sql + ";")

            cur.execute(f"SELECT * FROM `{tbl}`")
            rows = cur.fetchall()
            if rows:
                cols = list(rows[0].keys())
                col_list = ", ".join(f"`{c}`" for c in cols)
                for i in range(0, len(rows), 100):
                    chunk = rows[i : i + 100]
                    values_sql = ",\n".join(
                        "(" + ", ".join(_sql_literal(r[c]) for c in cols) + ")"
                        for r in chunk
                    )
                    lines.append(f"INSERT INTO `{tbl}` ({col_list}) VALUES\n{values_sql};")
            lines.append("")

    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("-- End of EduMatch PH SQL Backup")
    return "\n".join(lines) + "\n"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        out_path = os.path.abspath(sys.argv[1])
    else:
        backup_dir = os.path.join(here, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(backup_dir, f"edumatch_backup_{stamp}.sql")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sql_text = generate_sql_backup(record_event=False)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(sql_text)
    print(f"Backup saved: {out_path} ({len(sql_text.encode('utf-8')):,} bytes)")


if __name__ == "__main__":
    main()
