# ML model tests for EduMatch PH (ML-001 to ML-008 in the documentation).
# Run from inside edumatch_backend_v2/ with MySQL/MariaDB running and the schema loaded:
#     python test_ml.py [path/to/edumatch_synthetic_dataset.csv]
# The dataset is produced by train_edumatch.py. If no path is given, the script looks
# in ./data/, ./ and ../ml/ for edumatch_synthetic_dataset.csv.
import math
import os
import sys

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from app import app
from db import db
from eligibility import check_eligibility
from ranking import FEATURES, MODEL, _row, predict_priority

SEED = 42
results = []


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"   -> {detail}"))


def find_dataset():
    if len(sys.argv) > 1:
        return sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    for folder in (os.path.join(here, "data"), here, os.path.join(here, "..", "ml"),
                   os.path.join(here, "..")):
        p = os.path.join(folder, "edumatch_synthetic_dataset.csv")
        if os.path.exists(p):
            return p
    sys.exit("Dataset not found. Pass the path to edumatch_synthetic_dataset.csv")


df = pd.read_csv(find_dataset())
elig = df[df.eligible == 1]
X, y = elig[FEATURES], elig["priority_target"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.20, random_state=SEED)
kf = KFold(5, shuffle=True, random_state=SEED)

print("--- ML-001  Accuracy on the designated test set")
test_mae = mean_absolute_error(yte, MODEL.predict(Xte))
check(f"Test set has 24 rows (92 train / 24 test)", len(Xte) == 24 and len(Xtr) == 92, (len(Xtr), len(Xte)))
check(f"Test MAE {test_mae:.2f} is at most 6.0", test_mae <= 6.0, test_mae)
cv_lr = -cross_val_score(LinearRegression(), Xtr, ytr, cv=kf, scoring="neg_mean_absolute_error").mean()
cv_base = -cross_val_score(DummyRegressor(strategy="mean"), Xtr, ytr, cv=kf,
                           scoring="neg_mean_absolute_error").mean()
check(f"5-fold CV MAE {cv_lr:.2f} is lower than the mean-prediction baseline {cv_base:.2f}",
      cv_lr < cv_base, (cv_lr, cv_base))

print("--- ML-002  A new input produces a score")
school = {"scale_best": 1, "scale_passing": 3, "gwa_limit": 2.0, "min_entrance": 80,
          "income_cap": 300000, "higher_is_better": 0}
new = {"gwa": 1.5, "entrance_score": 90, "household_income": 150000}
score = predict_priority(new, school)
check(f"New applicant scores {score}, a number between 0 and 100",
      isinstance(score, float) and 0 <= score <= 100, score)
check("The same input gives the same score again", predict_priority(new, school) == score)

print("--- ML-003  Missing or invalid input gives an error and no score")
bad_cases = {"missing entrance_score": {"gwa": 1.5, "household_income": 150000},
             "missing household_income": {"gwa": 1.5, "entrance_score": 90},
             "text in gwa": {**new, "gwa": "abc"},
             "empty gwa": {**new, "gwa": None}}
for label, bad in bad_cases.items():
    try:
        got = predict_priority(bad, school)
        check(f"{label}: no score is returned", False, f"returned {got}")
    except Exception as e:
        check(f"{label}: error raised, no score ({type(e).__name__})", True)
with app.test_client() as c:
    c.post("/api/login", json={"organization_id": "uclm", "email": "alicia.ramos@uclm.edu.ph",
                               "password": "admin123"})
    pid = c.post("/api/scholarships", json={
        "scholarship_name": "TEST ML Input", "provider": "Test", "grade_scale": "COLLEGE_1_5",
        "gwa_limit": 2.6, "income_cap": 500000, "eligible_field": "ANY", "eligible_years": "1,2,3,4",
        "location_req": "Nationwide", "min_entrance": 60, "available_slots": 2, "status": "Open",
        "application_deadline": "2026-12-31"}).get_json()["scholarship_id"]
    r = c.post(f"/api/scholarships/{pid}/applicants", json={
        "full_name": "No Entrance", "gwa": 1.6, "household_income": 200000,
        "course": "BS Computer Science", "year_level": 1, "location": "Cebu City"})
    j = r.get_json(silent=True) or {}
    check("API rejects an applicant with no entrance_score (400, plain message)",
          r.status_code == 400 and "error" in j, (r.status_code, j))
    r = c.post(f"/api/scholarships/{pid}/applicants", json={
        "full_name": "Bad GWA", "gwa": "abc", "entrance_score": 88, "household_income": 200000,
        "course": "BS Computer Science", "year_level": 1, "location": "Cebu City"})
    check("API rejects a non-numeric GWA (400)", r.status_code == 400, r.get_json(silent=True))
    check("Rejected applicants were not saved", c.get(f"/api/scholarships/{pid}/applicants").get_json() == [])

print("--- ML-004  The saved model loads and has a fixed shape")
check("Model loaded at start-up (ranking.py import)", MODEL is not None and hasattr(MODEL, "predict"))
check("Model is Linear Regression with 6 coefficients", type(MODEL).__name__ == "LinearRegression"
      and len(MODEL.coef_) == 6)
check("Coefficients match the documented formula",
      abs(MODEL.intercept_ - (-83.8964)) < 1e-3 and abs(MODEL.coef_[0] - 2.360728) < 1e-5
      and abs(MODEL.coef_[1] - 0.847749) < 1e-5 and abs(MODEL.coef_[2] - (-0.00006013)) < 1e-8
      and abs(MODEL.coef_[3] - (-1.698473)) < 1e-5 and abs(MODEL.coef_[4] - (-0.146003)) < 1e-5
      and abs(MODEL.coef_[5] - 0.00001956) < 1e-8, (MODEL.intercept_, MODEL.coef_))

print("--- ML-005  Rule engine agrees with an independent re-check on all 500 pairs")
agree = 0
for _, r in df.iterrows():
    applicant = {"gwa": r.gwa, "entrance_score": r.entrance_score, "household_income": r.household_income,
                 "course": r.course, "year_level": r.year_level, "location": r.location}
    program = {"eligible_years": r.sch_eligible_years, "higher_is_better": 1, "gwa_limit": r.sch_min_gwa,
               "income_cap": r.sch_income_cap, "eligible_field": r.sch_eligible_field,
               "location_req": r.sch_location_req, "min_entrance": r.sch_min_entrance}
    ok, _checks = check_eligibility(applicant, program)
    agree += int(ok == bool(r.eligible))
check(f"eligibility.py agrees with the dataset on {agree} of {len(df)} rows", agree == len(df) == 500, agree)

print("--- ML-006  Only eligible applicants reach the model")
with app.test_client() as c:
    c.post("/api/login", json={"organization_id": "uclm", "email": "alicia.ramos@uclm.edu.ph",
                               "password": "admin123"})
    gate = c.post("/api/scholarships", json={
        "scholarship_name": "TEST ML Gate", "provider": "Test", "grade_scale": "COLLEGE_1_5",
        "gwa_limit": 2.0, "income_cap": 300000, "eligible_field": "ANY", "eligible_years": "1,2,3,4",
        "location_req": "Nationwide", "min_entrance": 80, "available_slots": 2, "status": "Open",
        "application_deadline": "2026-12-31"}).get_json()["scholarship_id"]
    base = {"entrance_score": 90, "household_income": 150000, "course": "BS Computer Science",
            "year_level": 1, "location": "Cebu City"}
    for name, gwa, ent in [("Gate A", 1.4, 90), ("Gate B", 1.7, 85), ("Gate C Low GWA", 3.0, 90),
                           ("Gate D Low Entrance", 1.5, 50)]:
        c.post(f"/api/scholarships/{gate}/applicants", json={**base, "full_name": name, "gwa": gwa,
                                                            "entrance_score": ent})
    c.post(f"/api/scholarships/{gate}/screen")
    c.post(f"/api/scholarships/{gate}/rank")
    ranked = c.get(f"/api/scholarships/{gate}/shortlist").get_json()
    names = sorted(r["full_name"] for r in ranked)
    check("4 applicants screened, 2 ineligible: only the 2 eligible are ranked",
          names == ["Gate A", "Gate B"], names)
    with db() as (conn, cur):
        cur.execute("SELECT COUNT(*) AS n FROM ranking_results rr JOIN screening_results sr "
                    "ON sr.result_id = rr.result_id WHERE sr.scholarship_id=%s AND sr.eligible=0", (gate,))
        n_bad = cur.fetchone()["n"]
    check("No ranking row exists for an ineligible applicant", n_bad == 0, n_bad)
    scores = [r["priority_score"] for r in ranked]
    check("Ranked list is in descending order of priority score", scores == sorted(scores, reverse=True), scores)

print("--- ML-007  Features are assembled in the fixed order the model expects")
check("Feature order is fixed", FEATURES == ["gwa", "entrance_score", "household_income",
                                              "sch_min_gwa", "sch_min_entrance", "sch_income_cap"])
row = _row(new, school)
by_hand = MODEL.intercept_ + sum(c * row[f] for c, f in zip(MODEL.coef_, FEATURES))
check("Score equals intercept + sum(coefficient x feature) done by hand (clipped to 0-100)",
      abs(max(0, min(100, by_hand)) - score) < 0.01, (by_hand, score))
check("Score is clipped to the 0-100 range for extreme input",
      0 <= predict_priority({"gwa": 1.0, "entrance_score": 100, "household_income": 0}, school) <= 100 and
      0 <= predict_priority({"gwa": 3.0, "entrance_score": 0, "household_income": 9_000_000}, school) <= 100)

print("--- ML-008  'Why this score?' explanation")
with app.test_client() as c:
    c.post("/api/login", json={"organization_id": "uclm", "email": "alicia.ramos@uclm.edu.ph",
                               "password": "admin123"})
    first = ranked[0]["applicant_id"]
    ex = c.get(f"/api/scholarships/{gate}/applicants/{first}/explanation").get_json()
    total = sum(e["effect_points"] for e in ex["effects"])
    pool_avg = sum(scores) / len(scores)
    check("Effects add up to (score - pool average score)", abs(total - (ex["priority_score"] - pool_avg)) < 0.1,
          (total, ex["priority_score"], pool_avg))
    check("Explanation covers GWA, entrance score and household income",
          [e["feature"] for e in ex["effects"]] == ["gwa", "entrance_score", "household_income"])

with db() as (conn, cur):
    cur.execute("DELETE FROM scholarship_programs WHERE scholarship_name LIKE 'TEST ML%'")
    conn.commit()

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
