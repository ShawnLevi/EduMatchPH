# Run from inside edumatch_backend/:  python test_ranking.py
# No database needed. This proves ranking.py + the model file work on their own.
from ranking import predict_priority

# DOST S&T: senior high school average, 0-100, higher is better
ana = {"gwa": 90, "entrance_score": 85, "household_income": 250000}
mark = {"gwa": 89.5, "entrance_score": 81, "household_income": 310000}
st_scholarship = {"gwa_limit": 88, "min_entrance": 80, "income_cap": 400000,
                  "scale_best": 100, "scale_passing": 75}

print("Ana :", predict_priority(ana, st_scholarship), "(expected 32.27)")
print("Mark:", predict_priority(mark, st_scholarship), "(expected 24.1)")
