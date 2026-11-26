from reference import LOCALITIES

STEM_COURSES = {
    "BS Architecture",
    "BS Biology",
    "BS Civil Engineering",
    "BS Computer Engineering",
    "BS Computer Science",
    "BS Electrical Engineering",
    "BS Electronics Engineering",
    "BS Industrial Engineering",
    "BS Information Systems",
    "BS Information Technology",
    "BS Mechanical Engineering",
    "BS Medical Technology",
    "BS Pharmacy",
}
BUSINESS_COURSES = {
    "BS Accountancy",
    "BS Business Administration",
    "BS Customs Administration",
    "BS Entrepreneurship",
    "BS Hospitality Management",
    "BS Management Accounting",
    "BS Tourism Management",
}
MARITIME_COURSES = {
    "BS Marine Engineering",
    "BS Marine Transportation",
    "BS Naval Architecture and Marine Engineering",
}
CRIMINOLOGY_COURSES = {"BS Criminology"}
NURSING_COURSES = {"BS Midwifery", "BS Nursing"}
EDUCATION_COURSES = {
    "BS Early Childhood Education",
    "BS Education",
    "BS Elementary Education",
    "BS Secondary Education",
}

FIELD_COURSES = {
    "STEM": STEM_COURSES,
    "BUSINESS": BUSINESS_COURSES,
    "MARITIME": MARITIME_COURSES,
    "CRIMINOLOGY": CRIMINOLOGY_COURSES,
    "NURSING": NURSING_COURSES,
    "EDUCATION": EDUCATION_COURSES,
}


def field_ok(course, eligible_field):
    if eligible_field == "ANY":
        return True
    allowed = FIELD_COURSES.get(eligible_field)
    return course in allowed if allowed is not None else False


def location_ok(applicant_location, location_req):
    if location_req == "Nationwide":
        return True
    if location_req == "Cebu":  # any city or municipality of Cebu Province
        return applicant_location in LOCALITIES
    return applicant_location == location_req  # one specific city/town


def check_eligibility(applicant, scholarship, required_reqs=None,
                      submitted_reqs=None):
    years_text = scholarship["eligible_years"]
    eligible_years = [int(y) for y in years_text.replace("|", ",").split(",")]

    # The program names its grade scale. On a scale where higher is better
    # (for example 0-100) the applicant needs AT LEAST the limit; where lower is
    # better (for example UCLM's 1.00-5.00) the applicant needs AT MOST the limit.
    if scholarship["higher_is_better"]:
        gwa_ok = applicant["gwa"] >= scholarship["gwa_limit"]
    else:
        gwa_ok = applicant["gwa"] <= scholarship["gwa_limit"]
    income_ok = applicant["household_income"] <= scholarship["income_cap"]
    fld_ok = field_ok(applicant["course"], scholarship["eligible_field"])
    year_ok = applicant["year_level"] in eligible_years
    loc_ok = location_ok(applicant["location"], scholarship["location_req"])
    ent_ok = applicant["entrance_score"] >= scholarship["min_entrance"]

    checks = {
        "GWA": (gwa_ok, applicant["gwa"], scholarship["gwa_limit"]),
        "Income": (income_ok, applicant["household_income"],
                   scholarship["income_cap"]),
        "Field": (fld_ok, applicant["course"],
                  scholarship["eligible_field"]),
        "Year Level": (year_ok, applicant["year_level"], years_text),
        "Location": (loc_ok, applicant["location"],
                     scholarship["location_req"]),
        "Entrance Score": (ent_ok, applicant["entrance_score"],
                           scholarship["min_entrance"]),
    }
    if required_reqs:
        submitted = {str(r).strip().lower() for r in (submitted_reqs or ())}
        for req in required_reqs:
            label = str(req).strip()
            if not label:
                continue
            met = label.lower() in submitted
            checks[label] = (met, "Submitted" if met else "Missing", "Required")
    is_eligible = all(v[0] for v in checks.values())
    return is_eligible, checks
