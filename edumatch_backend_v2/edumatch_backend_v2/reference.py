# One place for the fixed lists. The add-applicant form, the import,
# the validation, and the eligibility rules all read from here, so a new
# city or course is added in ONE file. Verify LOCALITIES against the
# official PSA list before the final paper.

# Cebu Province: 3 highly urbanized cities, 6 component cities, 44 municipalities.
# City names carry "City" (the same spelling the dataset uses).
CITIES = [
    "Cebu City", "Lapu-Lapu City", "Mandaue City",            # highly urbanized
    "Bogo City", "Carcar City", "Danao City", "Naga City",    # component cities
    "Talisay City", "Toledo City",
]
MUNICIPALITIES = [
    "Alcantara", "Alcoy", "Alegria", "Aloguinsan", "Argao", "Asturias",
    "Badian", "Balamban", "Bantayan", "Barili", "Boljoon", "Borbon",
    "Carmen", "Catmon", "Compostela", "Consolacion", "Cordova",
    "Daanbantayan", "Dalaguete", "Dumanjug", "Ginatilan", "Liloan",
    "Madridejos", "Malabuyoc", "Medellin", "Minglanilla", "Moalboal",
    "Oslob", "Pilar", "Pinamungajan", "Poro", "Ronda", "Samboan",
    "San Fernando", "San Francisco", "San Remigio", "Santa Fe",
    "Santander", "Sibonga", "Sogod", "Tabogon", "Tabuelan", "Tuburan",
    "Tudela",
]
LOCALITIES = sorted(CITIES + MUNICIPALITIES)

# A program's location requirement is one of these, or a single locality.
LOCATION_REQ_CHOICES = ["Nationwide", "Cebu"] + LOCALITIES

# Courses the system knows. STEM and BUSINESS membership lives in
# eligibility.py. A course outside this list is rejected, so a typo can't
# silently fail the Field rule.
COURSES = sorted([
    "AB Communication", "BS Accountancy", "BS Biology",
    "BS Business Administration", "BS Civil Engineering",
    "BS Computer Science", "BS Education", "BS Electronics Engineering",
    "BS Hospitality Management", "BS Information Technology",
    "BS Psychology",
])

FIELDS = ["ANY", "STEM", "BUSINESS"]
STATUSES = ["Open", "Screening", "Ranking", "Closed"]
