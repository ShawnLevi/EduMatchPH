# Input checks. Each function returns (clean_data, None) when the input is
# good, or (None, "plain-language message") when it is not.
import datetime

from reference import (COURSES, FIELDS, LOCALITIES, LOCATION_REQ_CHOICES,
                       STATUSES)


def _number(data, key, low, high, whole=False):
    value = data.get(key)
    if value is None or value == "" or isinstance(value, bool):
        return None, f"{key} is required"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None, f"{key} must be a number"
    if value != value or value in (float("inf"), float("-inf")):
        return None, f"{key} must be a real number"
    if not low <= value <= high:
        return None, f"{key} must be between {low:g} and {high:g}"
    if whole:
        if value != int(value):
            return None, f"{key} must be a whole number"
        return int(value), None
    return value, None


def clean_applicant(data, scale):
    """scale is the program's grade scale (min_value and max_value)."""
    if not isinstance(data, dict):
        return None, "Send the applicant as a JSON object"
    name = str(data.get("full_name") or "").strip()
    if not name:
        return None, "full_name is required"
    if len(name) > 150:
        return None, "full_name must be 150 characters or fewer"

    gwa, err = _number(data, "gwa", float(scale["min_value"]), float(scale["max_value"]))
    if err:
        return None, err
    entrance, err = _number(data, "entrance_score", 0, 100, whole=True)
    if err:
        return None, err
    income, err = _number(data, "household_income", 0, 100_000_000)
    if err:
        return None, err
    year, err = _number(data, "year_level", 1, 4, whole=True)
    if err:
        return None, err

    course = str(data.get("course") or "").strip()
    if course not in COURSES:
        return None, "course must be one of the listed courses (see /api/meta)"
    location = str(data.get("location") or "").strip()
    if location not in LOCALITIES:
        return None, ("location must be a city or municipality of Cebu "
                      "Province (see /api/meta)")
    return {
        "full_name": name, "gwa": gwa, "entrance_score": entrance,
        "household_income": income, "course": course,
        "year_level": year, "location": location,
    }, None


def _years(value):
    """Accept '1,2,3', '1|2|3', or a list. Return '1,2,3' (sorted, unique)."""
    if isinstance(value, (list, tuple)):
        parts = [str(v) for v in value]
    else:
        parts = str(value or "").replace("|", ",").split(",")
    try:
        years = sorted({int(p.strip()) for p in parts if p.strip()})
    except ValueError:
        return None
    if not years or any(y < 1 or y > 4 for y in years):
        return None
    return ",".join(str(y) for y in years)


def clean_program(data, scales):
    """scales maps scale_id to its row from the grade_scales table."""
    if not isinstance(data, dict):
        return None, "Send the program as a JSON object"
    name = str(data.get("scholarship_name") or "").strip()
    if not name:
        return None, "scholarship_name is required"
    provider = str(data.get("provider") or "").strip()

    scale_id = str(data.get("grade_scale") or "")
    scale = scales.get(scale_id)
    if scale is None:
        return None, ("grade_scale must be one of: "
                      + ", ".join(sorted(scales)))
    gwa_limit, err = _number(data, "gwa_limit", float(scale["min_value"]),
                             float(scale["max_value"]))
    if err:
        return None, err
    income_cap, err = _number(data, "income_cap", 1, 100_000_000)
    if err:
        return None, err
    min_entrance, err = _number(data, "min_entrance", 0, 100, whole=True)
    if err:
        return None, err
    slots, err = _number(data, "available_slots", 0, 100_000, whole=True)
    if err:
        return None, err

    field = str(data.get("eligible_field") or "")
    if field not in FIELDS:
        return None, "eligible_field must be ANY, STEM, or BUSINESS"
    years = _years(data.get("eligible_years"))
    if years is None:
        return None, "eligible_years must list year levels 1 to 4, like 1,2,3,4"
    location_req = str(data.get("location_req") or "").strip()
    if location_req not in LOCATION_REQ_CHOICES:
        return None, ("location_req must be Nationwide, Cebu, or one Cebu "
                      "city or municipality")
    status = str(data.get("status") or "Open")
    if status not in STATUSES:
        return None, "status must be Open, Screening, Ranking, or Closed"

    deadline = data.get("application_deadline") or None
    if deadline is not None:
        try:
            datetime.date.fromisoformat(str(deadline))
        except ValueError:
            return None, "application_deadline must look like 2026-12-31"
        deadline = str(deadline)
    return {
        "scholarship_name": name, "provider": provider or None,
        "grade_scale": scale_id, "gwa_limit": gwa_limit, "income_cap": income_cap,
        "eligible_field": field, "eligible_years": years,
        "location_req": location_req, "min_entrance": min_entrance,
        "available_slots": slots, "status": status,
        "application_deadline": deadline,
    }, None
