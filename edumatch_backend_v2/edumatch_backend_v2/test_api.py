# Run from inside edumatch_backend/ with MySQL running and the schema loaded:
#     python test_api.py
# It talks to the real database through Flask's test client (no server needed),
# prints PASS or FAIL for every check, and removes the programs it creates.
import io
import os
import subprocess
import sys

import openpyxl

from app import app
from db import db
from ranking import MODEL, FEATURES

results = []


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"   -> {detail}"))


def login(client, org, email, password="admin123"):
    return client.post("/api/login", json={
        "organization_id": org, "email": email, "password": password})


def new_client(org="uclm"):
    c = app.test_client()
    email = {"uclm": "alicia.ramos@uclm.edu.ph",
             "dost": "marco.villanueva@dost.gov.ph"}[org]
    assert login(c, org, email).status_code == 200
    return c


GOOD = dict(full_name="Test Person", gwa=1.6, entrance_score=88,
            household_income=200000, course="BS Computer Science",
            year_level=1, location="Cebu City")
PROGRAM = dict(scholarship_name="TEST Program", provider="Test", grade_scale="COLLEGE_1_5", gwa_limit=2.6,
               income_cap=500000, eligible_field="ANY",
               eligible_years="1,2,3,4", location_req="Nationwide",
               min_entrance=60, available_slots=2, status="Open",
               application_deadline="2026-12-31")


def make_program(c, **changes):
    r = c.post("/api/scholarships", json={**PROGRAM, **changes})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["scholarship_id"]


def error_ok(r, code):
    j = r.get_json(silent=True)
    return r.status_code == code and isinstance(j, dict) and "error" in j


try:
    print("--- Login and access rules")
    anon = app.test_client()
    check("No login -> 401 JSON", error_ok(anon.get("/api/scholarships"), 401))
    check("Wrong password -> 401",
          error_ok(login(anon, "uclm", "alicia.ramos@uclm.edu.ph", "nope"), 401))
    check("UCLM admin cannot log in to DOST",
          error_ok(login(anon, "dost", "alicia.ramos@uclm.edu.ph"), 401))
    uclm, dost = new_client("uclm"), new_client("dost")
    me = uclm.get("/api/me").get_json()
    check("/api/me shows the organization", me["organization_id"] == "uclm")
    lst = uclm.get("/api/scholarships").get_json()
    check("UCLM sees only its 3 seeded programs (or more of its own)",
          all(s["organization_id"] == "uclm" for s in lst) and len(lst) >= 3)
    check("Asking for another organization -> 403",
          error_ok(uclm.get("/api/scholarships?organization_id=dost"), 403))
    check("UCLM cannot open a DOST program (404)",
          error_ok(uclm.get("/api/scholarships/4"), 404))
    check("UCLM cannot screen a DOST program (404)",
          error_ok(uclm.post("/api/scholarships/4/screen"), 404))
    check("UCLM cannot read a DOST shortlist (404)",
          error_ok(uclm.get("/api/scholarships/4/shortlist"), 404))
    tmp = new_client("uclm")
    tmp.post("/api/logout")
    check("After logout -> 401", error_ok(tmp.get("/api/scholarships"), 401))
    check("Unknown route -> JSON 404", error_ok(uclm.get("/api/nothing"), 404))
    check("Wrong method -> JSON 405", error_ok(uclm.delete("/api/scholarships/1"), 405))

    print("--- Input validation")
    pid = make_program(uclm)
    url = f"/api/scholarships/{pid}/applicants"
    r = uclm.post(url, json=GOOD)
    check("Valid applicant -> 201", r.status_code == 201, r.get_json())
    bad = {
        "GWA 6 (above 5)": {**GOOD, "gwa": 6},
        "GWA 0.5 (below 1)": {**GOOD, "gwa": 0.5},
        "GWA text": {**GOOD, "gwa": "abc"},
        "negative income": {**GOOD, "household_income": -5},
        "year level 9": {**GOOD, "year_level": 9},
        "empty name": {**GOOD, "full_name": "  "},
        "missing gwa": {k: v for k, v in GOOD.items() if k != "gwa"},
        "unknown course": {**GOOD, "full_name": "B", "course": "BS Computer Sience"},
        "location outside Cebu": {**GOOD, "full_name": "C", "location": "Manila"},
        "entrance 88.5": {**GOOD, "full_name": "D", "entrance_score": 88.5},
    }
    for label, body in bad.items():
        check(f"Rejected: {label}", error_ok(uclm.post(url, json=body), 400))
    check("Rejected: no JSON body", error_ok(uclm.post(url), 400))
    check("Duplicate applicant -> 409", error_ok(uclm.post(url, json=GOOD), 409))
    check("Unknown scholarship -> 404",
          error_ok(uclm.post("/api/scholarships/9999/applicants", json=GOOD), 404))
    check("Unknown scholarship shortlist -> 404",
          error_ok(uclm.get("/api/scholarships/9999/shortlist"), 404))
    check("Unknown scholarship screening details -> 404",
          error_ok(uclm.get("/api/scholarships/9999/screening"), 404))

    print("--- Screening and ranking: the expected numbers")
    r = uclm.post("/api/scholarships/1/screen")
    first = r.get_json()
    again = uclm.post("/api/scholarships/1/screen").get_json()
    check("Screening twice gives the same count (no duplicates)",
          len(first) == len(again))
    det = uclm.get("/api/scholarships/1/screening").get_json()
    by = {d["full_name"]: d for d in det}
    juan = next(v for k, v in by.items() if k.startswith("Juan"))
    maria = next(v for k, v in by.items() if k.startswith("Maria"))
    check("Juan eligible", juan["eligible"] is True)
    failed = [x for x in maria["reasons"] if not x["met"]]
    check("Maria not eligible, fails only Entrance Score (82 vs 85)",
          maria["eligible"] is False and len(failed) == 1
          and failed[0]["criterion_name"] == "Entrance Score"
          and failed[0]["applicant_value"] == "82", failed)
    check("Six reasons per applicant", all(len(d["reasons"]) == 6 for d in det))
    check("Status becomes Screening",
          uclm.get("/api/scholarships/1").get_json()["status"] == "Screening")

    check("Rank before screening -> 400",
          error_ok(uclm.post(f"/api/scholarships/{make_program(uclm)}/rank"), 400))

    dost.post("/api/scholarships/4/screen")
    rk = dost.post("/api/scholarships/4/rank").get_json()
    check("Ranking counts", rk == {"ranked_count": 2, "shortlisted": 2,
                                   "waitlisted": 0}, rk)
    sl = dost.get("/api/scholarships/4/shortlist").get_json()
    check("Ana 32.27 is #1, Mark 24.1 is #2",
          [(s["full_name"], s["priority_score"], s["rank_position"]) for s in sl][:2]
          == [("Ana Villareal", 32.27, 1), ("Mark Tan", 24.1, 2)], sl)
    check("priority_score is a number, not text",
          all(isinstance(s["priority_score"], float) for s in sl))
    check("Ranking twice gives the same list",
          dost.post("/api/scholarships/4/rank").status_code == 200
          and dost.get("/api/scholarships/4/shortlist").get_json() == sl)
    check("Status becomes Ranking",
          dost.get("/api/scholarships/4").get_json()["status"] == "Ranking")

    print("--- Waitlist (1 slot) and clearing rules")
    prog4 = dost.get("/api/scholarships/4").get_json()
    edit = {k: prog4[k] for k in PROGRAM if k in prog4}
    edit["eligible_years"] = prog4["eligible_years"]
    r = dost.put("/api/scholarships/4", json={**edit, "available_slots": 1, "status": "Open"})
    check("Changing only slots clears ranking, keeps screening",
          r.get_json()["ranking_cleared"] and not r.get_json()["screening_cleared"],
          r.get_json())
    check("Screening details still there",
          len(dost.get("/api/scholarships/4/screening").get_json()) == 2)
    dost.post("/api/scholarships/4/rank")
    sl = dost.get("/api/scholarships/4/shortlist").get_json()
    check("1 slot: Ana SHORTLIST, Mark WAITLIST",
          [s["status"] for s in sl] == ["SHORTLIST", "WAITLIST"], sl)
    ex = dost.get(f"/api/scholarships/4/applicants/{sl[1]['applicant_id']}/explanation").get_json()
    pool_scores = [s["priority_score"] for s in sl]
    total = sum(e["effect_points"] for e in ex["effects"])
    check("Explanation effects add up to score minus pool average",
          abs(total - (ex["priority_score"] - sum(pool_scores) / 2)) < 0.1,
          (total, ex))
    check("Explanation names the three applicant inputs",
          [e["feature"] for e in ex["effects"]] ==
          ["gwa", "entrance_score", "household_income"])
    dost.post("/api/scholarships/4/screen")
    check("Re-screening clears the old ranking",
          dost.get("/api/scholarships/4/shortlist").get_json() == [])
    check("Explanation before ranking -> 400",
          error_ok(dost.get(f"/api/scholarships/4/applicants/{sl[0]['applicant_id']}/explanation"), 400))
    r2 = dost.put("/api/scholarships/4", json={**edit, "gwa_limit": 1.9})
    check("Changing gwa_limit clears screening and ranking",
          r2.get_json()["screening_cleared"] and r2.get_json()["ranking_cleared"])
    dost.put("/api/scholarships/4", json={**edit})
    dost.post("/api/scholarships/4/screen")
    dost.post("/api/scholarships/4/rank")

    print("--- Location rules")
    pc = make_program(uclm, scholarship_name="TEST Cebu", location_req="Cebu")
    uclm.post(f"/api/scholarships/{pc}/applicants", json={**GOOD, "full_name": "Santander Student", "location": "Santander"})
    uclm.post(f"/api/scholarships/{pc}/screen")
    d = uclm.get(f"/api/scholarships/{pc}/screening").get_json()[0]
    check("Santander student passes a 'Cebu' program", d["eligible"] is True, d)
    pcc = make_program(uclm, scholarship_name="TEST CebuCity", location_req="Cebu City")
    uclm.post(f"/api/scholarships/{pcc}/applicants", json={**GOOD, "full_name": "Danao Student", "location": "Danao City"})
    uclm.post(f"/api/scholarships/{pcc}/screen")
    d = uclm.get(f"/api/scholarships/{pcc}/screening").get_json()[0]
    check("Danao student fails a 'Cebu City' program on Location",
          not d["eligible"] and [x["criterion_name"] for x in d["reasons"] if not x["met"]] == ["Location"], d)

    print("--- GWA scale: 1.00 is best, a higher number is worse")
    pg = make_program(uclm, scholarship_name="TEST GWA Scale", gwa_limit=1.5)
    gurl = f"/api/scholarships/{pg}"
    for nm, g in [("Scale Better", 1.2), ("Scale Equal", 1.5), ("Scale Worse", 2.0)]:
        uclm.post(gurl + "/applicants", json={**GOOD, "full_name": nm, "gwa": g})
    uclm.post(gurl + "/screen")
    gd = {d["full_name"]: d for d in uclm.get(gurl + "/screening").get_json()}
    check("GWA 1.2 and 1.5 pass a maximum of 1.5", gd["Scale Better"]["eligible"] and gd["Scale Equal"]["eligible"], gd)
    gw = [x["criterion_name"] for x in gd["Scale Worse"]["reasons"] if not x["met"]]
    check("GWA 2.0 fails a maximum of 1.5, on GWA only", not gd["Scale Worse"]["eligible"] and gw == ["GWA"], gd["Scale Worse"])

    print("--- The six criteria: each one has a case that fails and a case that passes")
    # GWA: tested above ("GWA scale"). Location: tested above ("Location rules").
    # This block covers Income, Field, Year Level and Entrance Score. Each
    # failing applicant breaks exactly ONE rule, so the reason must name only it.
    p6 = make_program(uclm, scholarship_name="TEST Six Criteria", gwa_limit=2.0,
                      income_cap=300000, eligible_field="STEM",
                      eligible_years="1,2", min_entrance=85)
    u6 = f"/api/scholarships/{p6}"
    six = [
        ("Six All Pass", {}),
        ("Six Income Over", {"household_income": 350000}),
        ("Six Income Equal", {"household_income": 300000}),
        ("Six Field Wrong", {"course": "BS Business Administration"}),
        ("Six Year Wrong", {"year_level": 3}),
        ("Six Year Second", {"year_level": 2}),
        ("Six Entrance Low", {"entrance_score": 84}),
        ("Six Entrance Equal", {"entrance_score": 85}),
    ]
    for nm, change in six:
        uclm.post(u6 + "/applicants", json={**GOOD, "full_name": nm, **change})
    uclm.post(u6 + "/screen")
    sx = {d["full_name"]: d for d in uclm.get(u6 + "/screening").get_json()}

    def failed_on(name):
        return [x["criterion_name"] for x in sx[name]["reasons"] if not x["met"]]

    check("All six criteria met -> eligible, no reason failed",
          sx["Six All Pass"]["eligible"] and failed_on("Six All Pass") == [], sx["Six All Pass"])
    check("Income 350000 fails a cap of 300000, on Income only",
          not sx["Six Income Over"]["eligible"] and failed_on("Six Income Over") == ["Income"], sx["Six Income Over"])
    check("Income exactly at the cap (300000) passes",
          sx["Six Income Equal"]["eligible"], sx["Six Income Equal"])
    check("A business course fails a STEM program, on Field only",
          not sx["Six Field Wrong"]["eligible"] and failed_on("Six Field Wrong") == ["Field"], sx["Six Field Wrong"])
    check("Year 3 fails a program for years 1 and 2, on Year Level only",
          not sx["Six Year Wrong"]["eligible"] and failed_on("Six Year Wrong") == ["Year Level"], sx["Six Year Wrong"])
    check("Year 2 passes a program for years 1 and 2",
          sx["Six Year Second"]["eligible"], sx["Six Year Second"])
    check("Entrance 84 fails a minimum of 85, on Entrance Score only",
          not sx["Six Entrance Low"]["eligible"] and failed_on("Six Entrance Low") == ["Entrance Score"], sx["Six Entrance Low"])
    check("Entrance exactly at the minimum (85) passes",
          sx["Six Entrance Equal"]["eligible"], sx["Six Entrance Equal"])
    check("Every applicant has all six criteria recorded",
          all(len(d["reasons"]) == 6 for d in sx.values()), sx)

    print("--- Programs: add, edit, closed")
    check("Invalid program -> 400",
          error_ok(uclm.post("/api/scholarships", json={**PROGRAM, "gwa_limit": 6}), 400))
    check("Invalid location_req -> 400",
          error_ok(uclm.post("/api/scholarships", json={**PROGRAM, "location_req": "Manila"}), 400))
    check("'1|2|3' years are accepted and stored as 1,2,3",
          uclm.get(f"/api/scholarships/{make_program(uclm, eligible_years='1|2|3')}").get_json()["eligible_years"] == "1,2,3")
    pcl = make_program(uclm, scholarship_name="TEST Closed", status="Closed")
    check("Closed program cannot be screened", error_ok(uclm.post(f"/api/scholarships/{pcl}/screen"), 400))
    check("DOST cannot edit a UCLM program (404)",
          error_ok(dost.put(f"/api/scholarships/{pid}", json=PROGRAM), 404))
    meta = anon.get("/api/meta").get_json()
    check("/api/meta lists courses and localities, no login needed",
          "BS Computer Science" in meta["courses"] and "Santander" in meta["localities"] and "Alegria" in meta["localities"])

    print("--- Import from CSV and Excel")
    pi = make_program(uclm, scholarship_name="TEST Import")
    iurl = f"/api/scholarships/{pi}/applicants/import"
    header = "full_name,gwa,entrance_score,household_income,course,year_level,location\n"
    csv_text = (header + "Ana Import,1.72,90,150000,BS Accountancy,2,Mandaue City\n"
                "Bad Row,6,90,150000,BS Accountancy,2,Mandaue City\n"
                "Ana Import,1.72,90,150000,BS Accountancy,2,Mandaue City\n"
                "Ben Import,2.2,80,200000,BS Biology,3,Alegria\n")
    def upload(c, name, data, **form):
        return c.post(iurl, data={"file": (io.BytesIO(data), name), **form},
                      content_type="multipart/form-data")
    pv = upload(uclm, "a.csv", csv_text.encode()).get_json()
    check("CSV preview: 2 valid, 2 errors, nothing saved",
          pv["preview"] and pv["valid_rows"] == 2 and len(pv["errors"]) == 2 and pv["imported"] == 0, pv)
    check("Errors name the spreadsheet row", [e["row"] for e in pv["errors"]] == [3, 4], pv["errors"])
    with db() as (conn, cur):
        cur.execute("SELECT COUNT(*) n FROM applicants WHERE scholarship_id=%s", (pi,))
        check("Preview saved nothing", cur.fetchone()["n"] == 0)
    done = upload(uclm, "a.csv", csv_text.encode(), preview="false").get_json()
    check("Import saves the 2 valid rows", done["imported"] == 2, done)
    again = upload(uclm, "a.csv", csv_text.encode(), preview="false").get_json()
    check("Importing the same file again adds none (duplicates)", again["imported"] == 0, again)
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["Full Name", "GWA", "Entrance Score", "Household Income", "Course", "Year Level", "Location"])
    ws.append(["Excel Person", 1.52, 91, 120000, "BS Education", 1, "Santander"])
    buf = io.BytesIO(); wb.save(buf)
    x = upload(uclm, "a.xlsx", buf.getvalue(), preview="false").get_json()
    check("Excel (.xlsx) import works", x["imported"] == 1, x)
    check("Missing column -> 400", error_ok(upload(uclm, "b.csv", b"full_name,gwa\nA,1.8\n"), 400))
    check("Wrong file type -> 400", error_ok(upload(uclm, "b.pdf", b"x"), 400))
    check("Empty file -> 400", error_ok(upload(uclm, "b.csv", b""), 400))
    check("Cannot import into another organization's program (404)",
          error_ok(upload(dost, "a.csv", csv_text.encode()), 404))

    print("--- Tie-break, export and delete")
    pt = make_program(uclm, scholarship_name="TEST Ties", available_slots=2)
    turl = f"/api/scholarships/{pt}"
    people = [("=Tie Worst GWA", 2.2, 100000), ("Tie Best GWA Rich", 1.4, 300000),
              ("Tie Best GWA Poor", 1.4, 100000)]
    ids = {}
    for name, gwa, inc in people:
        r = uclm.post(turl + "/applicants", json={**GOOD, "full_name": name,
                      "gwa": gwa, "household_income": inc})
        ids[name] = r.get_json()["applicant_id"]
    check("Export before ranking -> 400", error_ok(uclm.get(turl + "/shortlist.csv"), 400))
    uclm.post(turl + "/screen")
    real_predict = sys.modules["app"].predict_priority
    sys.modules["app"].predict_priority = lambda a, s: 50.0  # force equal scores
    try:
        uclm.post(turl + "/rank")
    finally:
        sys.modules["app"].predict_priority = real_predict
    order = [r["full_name"] for r in uclm.get(turl + "/shortlist").get_json()]
    check("Equal scores: better GWA (lower number) first, then lower income",
          order == ["Tie Best GWA Poor", "Tie Best GWA Rich", "=Tie Worst GWA"], order)
    exp = uclm.get(turl + "/shortlist.csv")
    body = exp.get_data(as_text=True)
    check("CSV export downloads with a header and 3 rows",
          exp.status_code == 200 and exp.mimetype == "text/csv"
          and "attachment" in exp.headers.get("Content-Disposition", "")
          and len(body.strip().splitlines()) == 4, body[:200])
    check("CSV export neutralises a name that starts with =", "'=Tie Worst GWA" in body, body)
    check("Another organization cannot export (404)", error_ok(dost.get(turl + "/shortlist.csv"), 404))
    check("Another organization cannot delete (404)",
          error_ok(dost.delete(f"{turl}/applicants/{ids['=Tie Worst GWA']}"), 404))
    check("Deleting an unknown applicant -> 404", error_ok(uclm.delete(f"{turl}/applicants/999999"), 404))
    gone = uclm.delete(f"{turl}/applicants/{ids['=Tie Worst GWA']}")
    check("Delete works and says the ranking was cleared",
          gone.status_code == 200 and gone.get_json()["ranking_cleared"] is True, gone.get_json())
    with db() as (conn, cur):
        cur.execute("SELECT COUNT(*) n FROM applicants WHERE applicant_id=%s", (ids["=Tie Worst GWA"],))
        gone_n = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) n FROM screening_results WHERE applicant_id=%s", (ids["=Tie Worst GWA"],))
        sr_n = cur.fetchone()["n"]
        cur.execute("SELECT status FROM scholarship_programs WHERE scholarship_id=%s", (pt,))
        st = cur.fetchone()["status"]
    check("Applicant and their screening row are gone", gone_n == 0 and sr_n == 0)
    check("Old ranking is cleared and status returns to Screening",
          uclm.get(turl + "/shortlist").get_json() == [] and st == "Screening", st)

    print("--- Grade scale per program")
    sc = {x["scale_id"]: x for x in meta["grade_scales"]}
    check("/api/meta lists the three grade scales",
          set(sc) == {"SHS_PERCENT", "COLLEGE_1_5", "SCALE_5_BEST"}
          and sc["COLLEGE_1_5"]["higher_is_better"] is False
          and sc["SHS_PERCENT"]["higher_is_better"] is True, sc)
    p4 = dost.get("/api/scholarships/4").get_json()
    check("Program returns grade_scale, gwa_limit, label, direction",
          p4["grade_scale"] == "SHS_PERCENT" and float(p4["gwa_limit"]) == 88
          and p4["higher_is_better"] is True and p4["grade_scale_label"], p4)
    check("Unknown grade_scale -> 400",
          error_ok(uclm.post("/api/scholarships", json={**PROGRAM, "grade_scale": "NOPE"}), 400))
    check("Missing grade_scale -> 400",
          error_ok(uclm.post("/api/scholarships", json={k: v for k, v in PROGRAM.items() if k != "grade_scale"}), 400))
    check("gwa_limit 95 is outside the college 1-5 scale -> 400",
          error_ok(uclm.post("/api/scholarships", json={**PROGRAM, "gwa_limit": 95}), 400))
    ps = make_program(uclm, scholarship_name="TEST SHS", grade_scale="SHS_PERCENT", gwa_limit=85)
    surl = f"/api/scholarships/{ps}"
    check("Percent program accepts GWA 92",
          uclm.post(surl + "/applicants", json={**GOOD, "full_name": "Shs High", "gwa": 92}).status_code == 201)
    uclm.post(surl + "/applicants", json={**GOOD, "full_name": "Shs Equal", "gwa": 85})
    uclm.post(surl + "/applicants", json={**GOOD, "full_name": "Shs Low", "gwa": 80})
    check("Percent program rejects GWA 101",
          uclm.post(surl + "/applicants", json={**GOOD, "full_name": "Shs Odd", "gwa": 101}).status_code == 400)
    check("College program still rejects GWA 92",
          error_ok(uclm.post(f"/api/scholarships/{pg}/applicants", json={**GOOD, "full_name": "Wrong Scale", "gwa": 92}), 400))
    uclm.post(surl + "/screen")
    sd = {d["full_name"]: d for d in uclm.get(surl + "/screening").get_json()}
    check("Higher is better: 92 and 85 pass a limit of 85, 80 fails on GWA only",
          sd["Shs High"]["eligible"] and sd["Shs Equal"]["eligible"] and not sd["Shs Low"]["eligible"]
          and [x["criterion_name"] for x in sd["Shs Low"]["reasons"] if not x["met"]] == ["GWA"], sd)
    uclm.post(surl + "/rank")
    sl2 = uclm.get(surl + "/shortlist").get_json()
    check("92 ranks above 85 in a percent program", sl2[0]["full_name"] == "Shs High", sl2)
    ex2 = uclm.get(f"{surl}/applicants/{sl2[0]['applicant_id']}/explanation").get_json()
    check("Explanation label says higher is better",
          ex2["effects"][0]["label"] == "GWA (higher is better)" and ex2["effects"][0]["applicant_value"] == 92, ex2)
    check("Scale cannot change once the program has applicants",
          error_ok(uclm.put(surl, json={**PROGRAM, "grade_scale": "COLLEGE_1_5", "gwa_limit": 2.0}), 400))
    pe = make_program(uclm, scholarship_name="TEST Empty Scale", grade_scale="SHS_PERCENT", gwa_limit=80)
    check("Scale can change while the program is empty",
          uclm.put(f"/api/scholarships/{pe}", json={**PROGRAM, "grade_scale": "COLLEGE_1_5", "gwa_limit": 2.0}).status_code == 200)
    pr = make_program(uclm, scholarship_name="TEST Reversed", grade_scale="SCALE_5_BEST", gwa_limit=4.0)
    rurl = f"/api/scholarships/{pr}"
    uclm.post(rurl + "/applicants", json={**GOOD, "full_name": "Rev Good", "gwa": 4.5})
    uclm.post(rurl + "/applicants", json={**GOOD, "full_name": "Rev Bad", "gwa": 3.5})
    uclm.post(rurl + "/screen")
    rd = {d["full_name"]: d["eligible"] for d in uclm.get(rurl + "/screening").get_json()}
    check("Reversed scale (5.0 best): 4.5 passes a limit of 4.0, 3.5 fails", rd == {"Rev Good": True, "Rev Bad": False}, rd)
    from ranking import gwa_standing
    check("Standing: percent 90 -> 90, college 1.8 -> 90, 1.84 -> 89.5, 1.96 -> 88, reversed 4.0 -> 87.5",
          [round(gwa_standing(90, 100, 75), 2), round(gwa_standing(1.8, 1, 3), 2), round(gwa_standing(1.84, 1, 3), 2),
           round(gwa_standing(1.96, 1, 3), 2), round(gwa_standing(4, 5, 3), 2)] == [90, 90, 89.5, 88, 87.5])
    uclm.post(rurl + "/rank")
    csvtext = uclm.get(rurl + "/shortlist.csv").data.decode("utf-8-sig")
    check("CSV export has a grade_scale column", "grade_scale" in csvtext.splitlines()[0] and "SCALE_5_BEST" in csvtext)

    print("--- Model loads from any folder")
    code = f"import sys; sys.path.insert(0, r'{os.path.dirname(os.path.abspath(__file__))}'); import ranking; print('ok')"
    out = subprocess.run([sys.executable, "-c", code], cwd="/" if os.name != "nt" else "C:\\", capture_output=True, text=True)
    check("ranking.py loads when run from another folder", "ok" in out.stdout, out.stderr[-200:])
    check("Model uses the 6 features in fixed order",
          FEATURES == ["gwa", "entrance_score", "household_income", "sch_min_gwa", "sch_min_entrance", "sch_income_cap"]
          and len(MODEL.coef_) == 6)
finally:
    with db() as (conn, cur):
        cur.execute("DELETE FROM scholarship_programs WHERE scholarship_name LIKE 'TEST %'")
        conn.commit()

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
