import os
import warnings

import joblib
import pandas as pd

# Load the model relative to THIS file, so it works from any folder.
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "models", "edumatch_priority_model.joblib")
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    _bundle = joblib.load(_MODEL_PATH)
MODEL = _bundle["model"]
FEATURES = _bundle["features"]
# FEATURES is: ['gwa', 'entrance_score', 'household_income',
#               'sch_min_gwa', 'sch_min_entrance', 'sch_income_cap']
# The two GWA features are STANDINGS (0-100, higher is better), not raw grades.

# Training distribution bounds from train_edumatch.py (used for outlier alerts).
TRAIN_INCOME_MAX = 2_400_000.0
TRAIN_ENTRANCE_MIN = 40.0
TRAIN_STANDING_MIN = 75.0
TRAIN_STANDING_MAX = 100.0


def gwa_standing(value, best, passing):
    """Express a grade from ANY scale on one 0-100 line where higher is better:
    the best possible grade is 100 and the lowest passing grade is 75. This
    only re-labels grades inside ONE program (all its applicants share a scale);
    it never compares a grade from one scale with a grade from another.
    Senior high school average (best 100, passing 75): 90 -> 90.
    College GWA (best 1.00, passing 3.00): 1.80 -> 90."""
    best, passing = float(best), float(passing)
    return 100.0 - 25.0 * (best - float(value)) / (best - passing)


def program_standing(value, scholarship):
    return gwa_standing(value, scholarship["scale_best"],
                        scholarship["scale_passing"])


def _row(applicant, scholarship):
    # float() matters: MySQL hands back DECIMAL columns as Decimal objects.
    return {
        "gwa": program_standing(applicant["gwa"], scholarship),
        "entrance_score": float(applicant["entrance_score"]),
        "household_income": float(applicant["household_income"]),
        "sch_min_gwa": program_standing(scholarship["gwa_limit"], scholarship),
        "sch_min_entrance": float(scholarship["min_entrance"]),
        "sch_income_cap": float(scholarship["income_cap"]),
    }


def predict_priority(applicant, scholarship):
    X = pd.DataFrame([_row(applicant, scholarship)])[FEATURES]  # fixed order
    score = MODEL.predict(X)[0]
    return round(float(max(0, min(100, score))), 2)  # clip to 0-100


def predict_priorities(applicants, scholarship):
    """Batch-predict priority scores for a list of eligible applicants."""
    if not applicants:
        return []
    X = pd.DataFrame([_row(a, scholarship) for a in applicants])[FEATURES]
    scores = MODEL.predict(X)
    return [round(float(max(0, min(100, s))), 2) for s in scores]


def check_outlier_warnings(applicant, scholarship):
    """Identify inputs outside the synthetic model's training distribution or
    linear predictions that had to be clipped to [0, 100]."""
    r = _row(applicant, scholarship)
    X = pd.DataFrame([r])[FEATURES]
    raw_score = float(MODEL.predict(X)[0])
    warnings_out = []
    if r["household_income"] > TRAIN_INCOME_MAX:
        warnings_out.append(
            f"Household income (PHP {r['household_income']:,.0f}) exceeds the "
            f"model's training range (up to PHP {TRAIN_INCOME_MAX:,.0f}/yr)."
        )
    if r["entrance_score"] < TRAIN_ENTRANCE_MIN:
        warnings_out.append(
            f"Entrance score ({int(r['entrance_score'])}) is below the "
            f"model's training range ({int(TRAIN_ENTRANCE_MIN)}-99)."
        )
    if r["gwa"] < TRAIN_STANDING_MIN or r["gwa"] > TRAIN_STANDING_MAX:
        warnings_out.append(
            "Converted GWA standing falls outside the 75-100 passing-to-best "
            "training range."
        )
    if raw_score < 0.0 or raw_score > 100.0:
        warnings_out.append(
            f"Raw linear score ({raw_score:.2f}) fell outside 0-100 and was "
            f"clipped to {max(0.0, min(100.0, raw_score)):.2f}."
        )
    return warnings_out


# Plain labels for the three inputs that belong to the applicant.
APPLICANT_FEATURES = [
    ("gwa", "GWA"),
    ("entrance_score", "Entrance score"),
    ("household_income", "Household income"),
]


def explain_priority(applicant, pool, scholarship):
    """How much each of the applicant's three inputs moved the score up or
    down, compared with the average eligible applicant for the same program.
    Linear Regression: effect = coefficient x (value - pool average), worked
    out on the model's inputs (the GWA as a standing). The values shown are the
    ones the administrator typed (the GWA in the program's own scale). The
    program's own criteria are identical for everyone in the pool, so they
    never separate one applicant from another."""
    coefs = dict(zip(FEATURES, MODEL.coef_))
    rows = [_row(a, scholarship) for a in pool]
    mine = _row(applicant, scholarship)
    raw_mine = {"gwa": float(applicant["gwa"]),
                "entrance_score": float(applicant["entrance_score"]),
                "household_income": float(applicant["household_income"])}
    out = []
    for key, label in APPLICANT_FEATURES:
        average = sum(r[key] for r in rows) / len(rows)
        raw_average = sum(float(a[key]) for a in pool) / len(pool)
        if key == "gwa":
            label = ("GWA (higher is better)" if scholarship["higher_is_better"]
                     else "GWA (lower is better)")
        out.append({
            "feature": key,
            "label": label,
            "applicant_value": raw_mine[key],
            "pool_average": round(raw_average, 2),
            "effect_points": round(coefs[key] * (mine[key] - average), 2),
        })
    return out
