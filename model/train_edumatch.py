"""
EduMatch PH — Synthetic data generation, eligibility screening, and priority-scoring
model training. Aligned with the finalized ResCom & Data Science manuscripts:

  GWA SCALE: each program names its own grade scale (senior high school 0-100,
  college 1.00-5.00 where 1.00 is best, or another). The model never sees a raw
  grade. It sees a STANDING on one 0-100 line where higher is better:
      standing = 100 - 25 * (best - grade) / (best - passing)
  (best grade -> 100, lowest passing grade -> 75). Because the standing is a straight
  line of the grade, this script trains on standings directly: the "gwa" and
  "sch_min_gwa" columns below ARE standings. In the system, ranking.py converts a
  program's raw grades to standings first (see gwa_standing in ranking.py).

  ELIGIBILITY (rule-based, 6 core criteria): GWA, household income, degree field,
      year level, location, entrance examination score
  PRIORITY FEATURES (ML input): GWA, entrance score, household income + the
      corresponding scholarship thresholds. Course/year level/location are
      eligibility-only (categorical: met or not met, no notion of "exceeding").
  TARGET: researcher-defined synthetic priority score (NOT real award outcomes).
"""
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

SEED = 42
rng = np.random.default_rng(SEED)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

N_APPLICANTS, PER_APPLICANT = 100, 5   # 500 applicant-scholarship observations

STEM = {"BS Computer Science", "BS Information Technology", "BS Civil Engineering",
        "BS Electronics Engineering", "BS Biology"}
BUSINESS = {"BS Business Administration", "BS Accountancy", "BS Hospitality Management"}
COURSES = sorted(STEM | BUSINESS | {"BS Psychology", "BS Education", "AB Communication"})
LOCATIONS = ["Cebu City", "Mandaue City", "Lapu-Lapu City", "Talisay City",
             "Consolacion", "Minglanilla", "Danao City", "Toledo City"]

# ---------------- Scholarship programs ----------------
programs = pd.DataFrame([
 ("SCH-01","Academic Excellence Grant",   90, 500000,"ANY",     [1,2,3,4],"Nationwide",85),
 ("SCH-02","S&T Undergraduate Grant",     88, 400000,"STEM",    [1],      "Nationwide",80),
 ("SCH-03","Need-Based Tuition Subsidy",  80, 180000,"ANY",     [1,2,3,4],"Nationwide",60),
 ("SCH-04","Provincial Education Aid",    82, 250000,"ANY",     [1,2,3,4],"Cebu",      65),
 ("SCH-05","City Youth Scholarship",      83, 220000,"ANY",     [1,2],    "Cebu City", 65),
 ("SCH-06","Tech Industry Fellowship",    86, 800000,"STEM",    [2,3,4],  "Nationwide",75),
 ("SCH-07","Business Leaders Grant",      86, 700000,"BUSINESS",[2,3,4],  "Nationwide",72),
 ("SCH-08","Institutional Merit Award",   85, 900000,"ANY",     [1,2,3,4],"Nationwide",70),
 ("SCH-09","Engineering Excellence Fund", 89, 600000,"STEM",    [3,4],    "Nationwide",82),
 ("SCH-10","Community Service Grant",     80, 300000,"ANY",     [1,2,3,4],"Cebu",      60),
], columns=["scholarship_id","scholarship_name","min_gwa","income_cap","eligible_field",
            "eligible_years","location_req","min_entrance"])

# ---------------- Applicants ----------------
ability = rng.normal(0, 1, N_APPLICANTS)
gwa = np.round(np.clip(87 + 4.8*ability + rng.normal(0, 2.2, N_APPLICANTS), 75, 99), 2)
entrance = np.round(np.clip(74 + 11*ability + rng.normal(0, 6.5, N_APPLICANTS), 40, 99)).astype(int)
income = np.clip(np.round(rng.lognormal(12.15, 0.62, N_APPLICANTS), -2), 42000, 2400000).astype(int)
applicants = pd.DataFrame({
    "applicant_id": [f"APP-{1000+i}" for i in range(N_APPLICANTS)],
    "gwa": gwa, "entrance_score": entrance, "household_income": income,
    "course": rng.choice(COURSES, N_APPLICANTS),
    "year_level": rng.choice([1,2,3,4], N_APPLICANTS, p=[.34,.26,.22,.18]),
    "location": rng.choice(LOCATIONS, N_APPLICANTS, p=[.28,.18,.16,.12,.08,.08,.05,.05]),
})

def field_ok(c, f):
    return 1 if f=="ANY" else int(c in STEM) if f=="STEM" else int(c in BUSINESS)
def loc_ok(l, r):
    return 1 if r in ("Nationwide","Cebu") else int(l == r)

rows = []
for _, a in applicants.iterrows():
    for _, p in programs.sample(PER_APPLICANT, random_state=int(rng.integers(1e6))).iterrows():
        flags = {
            "meets_gwa":      int(a.gwa >= p.min_gwa),
            "meets_income":   int(a.household_income <= p.income_cap),
            "meets_field":    field_ok(a.course, p.eligible_field),
            "meets_year":     int(a.year_level in p.eligible_years),
            "meets_location": loc_ok(a.location, p.location_req),
            "meets_entrance": int(a.entrance_score >= p.min_entrance),
        }
        eligible = int(all(flags.values()))
        gm = np.clip((a.gwa - p.min_gwa) / (100 - p.min_gwa), 0, 1)
        em = np.clip((a.entrance_score - p.min_entrance) / (100 - p.min_entrance), 0, 1)
        need = np.clip(1 - a.household_income / p.income_cap, 0, 1)
        target = 100*(0.40*gm + 0.30*em + 0.30*need) + rng.normal(0, 2.5)
        rows.append({**a.to_dict(), "scholarship_id": p.scholarship_id,
                     "scholarship_name": p.scholarship_name, "sch_min_gwa": p.min_gwa,
                     "sch_income_cap": p.income_cap, "sch_eligible_field": p.eligible_field,
                     "sch_eligible_years": "|".join(map(str, p.eligible_years)),
                     "sch_location_req": p.location_req, "sch_min_entrance": p.min_entrance,
                     **flags, "eligible": eligible,
                     "priority_target": round(float(np.clip(target, 0, 100)), 2) if eligible else None})
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "edumatch_synthetic_dataset.csv"), index=False)

def reverify(r):
    yrs = [int(y) for y in r.sch_eligible_years.split("|")]
    return int(r.gwa >= r.sch_min_gwa and r.household_income <= r.sch_income_cap
               and field_ok(r.course, r.sch_eligible_field) and r.year_level in yrs
               and loc_ok(r.location, r.sch_location_req) and r.entrance_score >= r.sch_min_entrance)
agree = int((df.apply(reverify, axis=1) == df.eligible).sum())


def _spearman_rho(a, b):
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    if np.std(ra) == 0 or np.std(rb) == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


FEATURES = ["gwa","entrance_score","household_income","sch_min_gwa","sch_min_entrance","sch_income_cap"]
elig = df[df.eligible == 1].copy()
X, y = elig[FEATURES], elig["priority_target"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.20, random_state=SEED)
kf = KFold(5, shuffle=True, random_state=SEED)

grid = GridSearchCV(RandomForestRegressor(random_state=SEED),
    {"n_estimators":[100,200,300], "max_depth":[None,6,10], "min_samples_leaf":[1,3,5]},
    cv=kf, scoring="neg_mean_absolute_error").fit(Xtr, ytr)

models = {"Baseline (Mean)": DummyRegressor(strategy="mean"),
          "Linear Regression": LinearRegression(),
          "Random Forest (tuned)": RandomForestRegressor(random_state=SEED, **grid.best_params_)}
res = {}
for name, m in models.items():
    cv_mae = -cross_val_score(m, Xtr, ytr, cv=kf, scoring="neg_mean_absolute_error")
    m.fit(Xtr, ytr); pred = m.predict(Xte)
    rho = _spearman_rho(yte, pred)
    res[name] = {"cv_mae_mean": float(cv_mae.mean()), "cv_mae_std": float(cv_mae.std()),
                 "test_mae": float(mean_absolute_error(yte, pred)),
                 "test_rmse": float(np.sqrt(mean_squared_error(yte, pred))),
                 "test_r2": float(r2_score(yte, pred)), "spearman": float(rho)}

cands = {k: v for k, v in res.items() if not k.startswith("Baseline")}
best = min(cands, key=lambda k: cands[k]["cv_mae_mean"])
best_model = models[best]
resid = yte - best_model.predict(Xte)

rf = models["Random Forest (tuned)"]
imp = dict(zip(FEATURES, map(float, rf.feature_importances_)))
lr_std = LinearRegression().fit(StandardScaler().fit_transform(Xtr), ytr)
coef = dict(zip(FEATURES, map(float, lr_std.coef_)))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    p = best_model.predict(Xte)
    ax[0].scatter(yte, p, s=22, alpha=.75, color="#16213D")
    lo, hi = min(yte.min(), p.min()), max(yte.max(), p.max())
    ax[0].plot([lo, hi], [lo, hi], "--", color="#B8862B"); ax[0].set_xlabel("Target priority score")
    ax[0].set_ylabel("Predicted priority score"); ax[0].set_title(f"Predicted vs. Target ({best})")
    ax[1].hist(resid, bins=14, color="#16213D", edgecolor="white"); ax[1].axvline(0, color="#B8862B", ls="--")
    ax[1].set_xlabel("Residual (target - predicted)"); ax[1].set_ylabel("Count"); ax[1].set_title("Residual Distribution")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "model_evaluation_plots.png"), dpi=200); plt.close()
except ImportError:
    pass

joblib.dump({"model": best_model, "features": FEATURES, "model_name": best},
            os.path.join(OUT, "edumatch_priority_model.joblib"))

summary = {
  "observations": len(df), "applicants": N_APPLICANTS, "programs": len(programs),
  "eligible": int(df.eligible.sum()), "ineligible": int((1-df.eligible).sum()),
  "train_n": len(Xtr), "test_n": len(Xte),
  "fail_counts": {k.replace("meets_",""): int((df[k]==0).sum()) for k in
                  ["meets_gwa","meets_income","meets_field","meets_year","meets_location","meets_entrance"]},
  "eligibility_agreement": agree, "rf_best_params": grid.best_params_,
  "results": res, "best": best, "rf_importance": imp, "lr_std_coef": coef,
  "resid_mean": float(resid.mean()), "resid_std": float(resid.std()),
  "target_mean": float(y.mean()), "target_std": float(y.std()),
  "target_min": float(y.min()), "target_max": float(y.max()),
  "gwa_range": [float(applicants.gwa.min()), float(applicants.gwa.max())],
  "ent_range": [int(applicants.entrance_score.min()), int(applicants.entrance_score.max())],
  "inc_range": [int(applicants.household_income.min()), int(applicants.household_income.max())],
  "missing": int(df[FEATURES].isna().sum().sum()), "duplicates": int(df.duplicated().sum()),
}
with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2, default=str)
print(f"Regenerated successfully into: {OUT}")
