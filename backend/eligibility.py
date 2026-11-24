from reference import LOCALITIES

STEM_COURSES = {
    "BS Computer Science", "BS Information Technology",
    "BS Civil Engineering", "BS Electronics Engineering", "BS Biology",
}
BUSINESS_COURSES = {
    "BS Business Administration", "BS Accountancy",
    "BS Hospitality Management",
}


def field_ok(course, eligible_field):
    if eligible_field == "ANY":
        return True
    if eligible_field == "STEM":
        return course in STEM_COURSES
    if eligible_field == "BUSINESS":
        return course in BUSINESS_COURSES
    return False


def location_ok(applicant_location, location_req):
    if location_req == "Nationwide":
        return True
    if location_req == "Cebu":  # any city or municipality of Cebu Province
        return applicant_location in LOCALITIES
    return applicant_location == location_req  # one specific city/town


def check_eligibility(applicant, scholarship):
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
    is_eligible = all(v[0] for v in checks.values())
    return is_eligible, checks
