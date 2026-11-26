# Input checks. Each function returns (clean_data, None) when the input is
# good, or (None, "plain-language message") when it is not.
import datetime
import difflib
import re

from reference import (CITIES, COURSES, FIELDS, LOCALITIES,
                       LOCATION_REQ_CHOICES, STATUSES)


# Layer 2: Common Philippine / Cebu degree course shorthand aliases
COURSE_ALIASES = {
    "ABCOMM": "AB Communication",
    "BACOMM": "AB Communication",
    "ABCOMMUNICATION": "AB Communication",
    "ABENG": "AB English Language",
    "BAEL": "AB English Language",
    "BSA": "BS Accountancy",
    "BSACCT": "BS Accountancy",
    "BSARCH": "BS Architecture",
    "BSARKI": "BS Architecture",
    "BSBIO": "BS Biology",
    "BSBA": "BS Business Administration",
    "BSCE": "BS Civil Engineering",
    "BSCPE": "BS Computer Engineering",
    "BSCOE": "BS Computer Engineering",
    "BSCS": "BS Computer Science",
    "COMSCI": "BS Computer Science",
    "BSCRIM": "BS Criminology",
    "BSCA": "BS Customs Administration",
    "BSCUSTOMS": "BS Customs Administration",
    "BECED": "BS Early Childhood Education",
    "BSED": "BS Secondary Education",
    "BSEDUC": "BS Education",
    "BSEE": "BS Electrical Engineering",
    "BSECE": "BS Electronics Engineering",
    "BEED": "BS Elementary Education",
    "BSENTREP": "BS Entrepreneurship",
    "BSHM": "BS Hospitality Management",
    "BSHRM": "BS Hospitality Management",
    "BSIE": "BS Industrial Engineering",
    "BSIS": "BS Information Systems",
    "BSIT": "BS Information Technology",
    "BSMA": "BS Management Accounting",
    "BSMARE": "BS Marine Engineering",
    "BSMT": "BS Marine Transportation",
    "BSME": "BS Mechanical Engineering",
    "BSMEDTECH": "BS Medical Technology",
    "BMLS": "BS Medical Technology",
    "BSMLS": "BS Medical Technology",
    "BSM": "BS Midwifery",
    "BSNAME": "BS Naval Architecture and Marine Engineering",
    "BSN": "BS Nursing",
    "BSPHARM": "BS Pharmacy",
    "BSPSYCH": "BS Psychology",
    "BSSW": "BS Social Work",
    "BSTM": "BS Tourism Management",
    "BSTOURISM": "BS Tourism Management",
}


def _canon_key(text):
    """Canonical lowercase key: collapses punctuation, hyphens, and whitespace."""
    s = re.sub(r"\bb\.?\s*s\.?\b", "bs", str(text or "").lower())
    s = re.sub(r"\ba\.?\s*b\.?\b", "ab", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def _build_course_canon():
    out = {_canon_key(c): c for c in COURSES}
    for c in COURSES:
        if c.startswith("BS "):
            out[_canon_key("Bachelor of Science in " + c[3:])] = c
        elif c.startswith("AB "):
            out[_canon_key("Bachelor of Arts in " + c[3:])] = c
    return out


def _build_locality_canon():
    out = {_canon_key(loc): loc for loc in LOCALITIES}
    for city in CITIES:
        base = city[:-5] if city.endswith(" City") else city
        out[_canon_key(base)] = city
        out[_canon_key("City of " + base)] = city
    out["sta fe"] = "Santa Fe"
    out["sta. fe"] = "Santa Fe"
    return out


def resolve_smart_choice(raw, exact_choices, canon_map, alias_map,
                         low_err, label):
    """3-layer normalization for spreadsheet imports:
      Layer 1: Canonical key (case, extra spaces, hyphens, missing 'City').
      Layer 2: Shorthand / abbreviation lookup (e.g., BSIT, BSCS, BSMT).
      Layer 3: Two-tier fuzzy match (>= 0.85 auto-correct; 0.60-0.84 'Did you mean?').
    Returns (resolved_value, method_or_None, error_or_None).
    """
    text = str(raw or "").strip()
    if not text:
        return None, None, low_err
    if text in exact_choices:
        return text, None, None

    canon = _canon_key(text)
    if canon in canon_map:
        return canon_map[canon], "canonical", None

    if alias_map:
        compact = re.sub(r"[^A-Z0-9]", "", text.upper())
        if compact in alias_map and alias_map[compact] in exact_choices:
            return alias_map[compact], "alias", None

    # Layer 3: Two-tier fuzzy matching against canonical candidates
    best_val, best_score = None, 0.0
    candidates = [( _canon_key(c), c ) for c in exact_choices]
    if exact_choices is LOCALITIES:
        for city in CITIES:
            if city.endswith(" City"):
                candidates.append((_canon_key(city[:-5]), city))
    for cand_key, cand_val in candidates:
        score = difflib.SequenceMatcher(None, canon, cand_key).ratio()
        if score > best_score:
            best_score, best_val = score, cand_val

    if best_score >= 0.85 and best_val is not None:
        return best_val, "fuzzy", None
    if best_score >= 0.60 and best_val is not None:
        return None, None, f"Unknown {label} '{text}'. Did you mean '{best_val}'?"
    return None, None, low_err


LABELS = {
    "gwa": "GWA", "entrance_score": "Entrance score",
    "household_income": "Household income", "year_level": "Year level",
    "full_name": "Full name", "gwa_limit": "GWA limit",
    "income_cap": "Income cap", "min_entrance": "Minimum entrance score",
    "available_slots": "Available slots",
    "scholarship_name": "Scholarship name",
}


def _number(data, key, low, high, whole=False):
    label = LABELS.get(key, key)
    value = data.get(key)
    if value is None or value == "" or isinstance(value, bool):
        return None, f"{label} is required"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None, f"{label} must be a number"
    if value != value or value in (float("inf"), float("-inf")):
        return None, f"{label} must be a real number"
    if not low <= value <= high:
        return None, f"{label} must be between {low:g} and {high:g}"
    if whole:
        if value != int(value):
            return None, f"{label} must be a whole number"
        return int(value), None
    return value, None


def clean_applicant(data, scale):
    """scale is the program's grade scale (min_value and max_value)."""
    if not isinstance(data, dict):
        return None, "The applicant details were incomplete"
    name = str(data.get("full_name") or "").strip()
    if not name:
        return None, "Full name is required"
    if len(name) > 150:
        return None, "Full name must be 150 characters or fewer"

    gwa, err = _number(data, "gwa", float(scale["min_value"]), float(scale["max_value"]))
    if err:
        return None, err
    entrance, err = _number(data, "entrance_score", 0, 100, whole=True)
    if err:
        return None, err
    income, err = _number(data, "household_income", 0, 100_000_000)
    if err:
        return None, err
    year, err = _number(data, "year_level", 1, 5, whole=True)
    if err:
        return None, err

    course = str(data.get("course") or "").strip()
    if course not in COURSES:
        return None, "Choose a course from the list"
    location = str(data.get("location") or "").strip()
    if location not in LOCALITIES:
        return None, ("Location must be a city or municipality of Cebu "
                      "Province")
    return {
        "full_name": name, "gwa": gwa, "entrance_score": entrance,
        "household_income": income, "course": course,
        "year_level": year, "location": location,
    }, None


def clean_applicant_import(data, scale):
    """Spreadsheet import cleaner with 3-layer course & location normalization
    and 'Did you mean...?' suggestions. Returns (clean_dict, corrections, err)."""
    if not isinstance(data, dict):
        return None, [], "The applicant details were incomplete"
    name = re.sub(r"\s+", " ", str(data.get("full_name") or "").strip())
    if not name:
        return None, [], "Full name is required"
    if len(name) > 150:
        return None, [], "Full name must be 150 characters or fewer"

    gwa, err = _number(data, "gwa", float(scale["min_value"]), float(scale["max_value"]))
    if err:
        return None, [], err
    entrance, err = _number(data, "entrance_score", 0, 100, whole=True)
    if err:
        return None, [], err
    income_raw = data.get("household_income")
    if isinstance(income_raw, str):
        income_raw = re.sub(r"[₱,\s]", "", income_raw)
        data = {**data, "household_income": income_raw}
    income, err = _number(data, "household_income", 0, 100_000_000)
    if err:
        return None, [], err
    year_raw = data.get("year_level")
    if isinstance(year_raw, str):
        m_yr = re.match(r"^\s*([1-5])(?:st|nd|rd|th)?(?:\s*year)?\s*$", year_raw, re.I)
        if m_yr:
            data = {**data, "year_level": m_yr.group(1)}
    year, err = _number(data, "year_level", 1, 5, whole=True)
    if err:
        return None, [], err

    corrections = []
    raw_course = str(data.get("course") or "").strip()
    course, c_method, c_err = resolve_smart_choice(
        raw_course, COURSES, _build_course_canon(), COURSE_ALIASES,
        "Choose a course from the list", "course",
    )
    if c_err:
        return None, [], c_err
    if c_method and course != raw_course:
        corrections.append({"field": "course", "from": raw_course,
                            "to": course, "method": c_method})

    raw_loc = str(data.get("location") or "").strip()
    location, l_method, l_err = resolve_smart_choice(
        raw_loc, LOCALITIES, _build_locality_canon(), None,
        "Location must be a city or municipality of Cebu Province", "location",
    )
    if l_err:
        return None, [], l_err
    if l_method and location != raw_loc:
        corrections.append({"field": "location", "from": raw_loc,
                            "to": location, "method": l_method})

    return {
        "full_name": name, "gwa": gwa, "entrance_score": entrance,
        "household_income": income, "course": course,
        "year_level": year, "location": location,
    }, corrections, None


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
    if not years or any(y < 1 or y > 5 for y in years):
        return None
    return ",".join(str(y) for y in years)


def clean_program(data, scales):
    """scales maps scale_id to its row from the grade_scales table."""
    if not isinstance(data, dict):
        return None, "The program details were incomplete"
    name = str(data.get("scholarship_name") or "").strip()
    if not name:
        return None, "Scholarship name is required"
    provider = str(data.get("provider") or "").strip()
    if not provider:
        return None, "Provider is required"

    scale_id = str(data.get("grade_scale") or "")
    scale = scales.get(scale_id)
    if scale is None:
        return None, ("Choose a grade scale: "
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
        return None, ("Eligible field must be Any, STEM, Business, Maritime, "
                      "Criminology, Nursing or Education")
    years = _years(data.get("eligible_years"))
    if years is None:
        return None, "Choose at least one year level from 1 to 5"
    location_req = str(data.get("location_req") or "").strip()
    if location_req not in LOCATION_REQ_CHOICES:
        return None, ("Location requirement must be Nationwide, Cebu, or one "
                      "Cebu city or municipality")
    status = str(data.get("status") or "Open")
    if status not in STATUSES:
        return None, "Status must be Open, Screening, Ranking or Closed"

    deadline = data.get("application_deadline") or None
    if deadline is not None:
        try:
            datetime.date.fromisoformat(str(deadline))
        except ValueError:
            return None, "Application deadline must be a date like 2026-12-31"
        deadline = str(deadline)
    return {
        "scholarship_name": name, "provider": provider,
        "grade_scale": scale_id, "gwa_limit": gwa_limit, "income_cap": income_cap,
        "eligible_field": field, "eligible_years": years,
        "location_req": location_req, "min_entrance": min_entrance,
        "available_slots": slots, "status": status,
        "application_deadline": deadline,
    }, None
