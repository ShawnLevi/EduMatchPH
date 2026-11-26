"""
EduMatch PH — Reproducible End-to-End Performance & Latency Benchmark.
Measures Stage 1 rule-based screening, Stage 2 batch ML ranking, XAI
single-applicant explanation, and CSV export latencies across pool sizes
of 50, 200, and 500 applicants through Flask's test client + live MySQL.

Usage:
    python timing_test.py
"""
import io
import random
import time

from app import app
from db import db
from reference import COURSES, LOCALITIES

POOL_SIZES = [50, 200, 500]


def _ms(t0):
    return (time.perf_counter() - t0) * 1000.0


def run_benchmarks():
    rng = random.Random(42)
    with db() as (conn, cur):
        cur.execute("SELECT COALESCE(MAX(log_id), 0) AS mx FROM audit_logs")
        start_log_id = cur.fetchone()["mx"]

    client = app.test_client()
    r = client.post("/api/login", json={
        "organization_id": "uclm",
        "email": "alicia.ramos@uclm.edu.ph",
        "password": "admin123",
    })
    assert r.status_code == 200, f"Login failed: {r.get_json()}"

    print("EduMatch PH — End-to-End Performance Benchmark (Pooled MySQL + Batch ML)")
    print("-" * 82)
    print(f"{'Pool Size':>10} | {'CSV Import':>12} | {'Screen All':>12} | {'Rank (ML)':>12} | {'XAI Why?':>10} | {'Export CSV':>11}")
    print("-" * 82)

    try:
        for n in POOL_SIZES:
            pid = client.post("/api/scholarships", json={
                "scholarship_name": f"TEST Timing Benchmark {n}",
                "provider": "Benchmark",
                "grade_scale": "COLLEGE_1_5",
                "gwa_limit": 2.40,
                "income_cap": 400000,
                "eligible_field": "ANY",
                "eligible_years": "1,2,3,4,5",
                "location_req": "Cebu",
                "min_entrance": 70,
                "available_slots": 20,
                "status": "Open",
                "application_deadline": "2026-12-31",
            }).get_json()["scholarship_id"]

            lines = ["full_name,gwa,entrance_score,household_income,course,year_level,location"]
            for i in range(n):
                gwa = round(rng.uniform(1.15, 2.85), 2)
                ent = rng.randint(60, 99)
                inc = rng.randrange(60000, 480000, 5000)
                course = rng.choice(COURSES)
                yr = rng.randint(1, 5)
                loc = rng.choice(LOCALITIES)
                lines.append(f"Bench Applicant {i+1},{gwa},{ent},{inc},{course},{yr},{loc}")
            csv_bytes = ("\n".join(lines) + "\n").encode("utf-8")

            t0 = time.perf_counter()
            r_imp = client.post(
                f"/api/scholarships/{pid}/applicants/import",
                data={"file": (io.BytesIO(csv_bytes), "bench.csv"), "preview": "false"},
                content_type="multipart/form-data",
            )
            assert r_imp.status_code == 200 and r_imp.get_json()["imported"] == n
            t_import = _ms(t0)

            t0 = time.perf_counter()
            r_scr = client.post(f"/api/scholarships/{pid}/screen")
            assert r_scr.status_code == 200
            t_screen = _ms(t0)

            t0 = time.perf_counter()
            r_rnk = client.post(f"/api/scholarships/{pid}/rank")
            assert r_rnk.status_code == 200
            t_rank = _ms(t0)

            sl = client.get(f"/api/scholarships/{pid}/shortlist").get_json()
            first_id = sl[0]["applicant_id"]

            t0 = time.perf_counter()
            r_xai = client.get(f"/api/scholarships/{pid}/applicants/{first_id}/explanation")
            assert r_xai.status_code == 200
            t_xai = _ms(t0)

            t0 = time.perf_counter()
            r_exp = client.get(f"/api/scholarships/{pid}/shortlist.csv")
            assert r_exp.status_code == 200
            t_exp = _ms(t0)

            print(
                f"{n:>10} | {t_import:>9.1f} ms | {t_screen:>9.1f} ms | "
                f"{t_rank:>9.1f} ms | {t_xai:>7.1f} ms | {t_exp:>8.1f} ms"
            )
    finally:
        with db() as (conn, cur):
            cur.execute("DELETE FROM scholarship_programs WHERE scholarship_name LIKE 'TEST Timing Benchmark%'")
            cur.execute("DELETE FROM audit_logs WHERE log_id > %s", (start_log_id,))
            conn.commit()
    print("-" * 82)
    print("All benchmark runs completed and temporary rows cleaned up.")


if __name__ == "__main__":
    run_benchmarks()
