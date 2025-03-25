import re

# Keywords
keywords = {
    "Gender": ["male", "female", " man ", "woman", " men ", " men,", "women", "boy", "girl", "males", "females"],
    "Age": [" age ", "age,"," aged ", "years old", "year-old", "year olds", "elderly", "adults", "young", "youth"],
    "Patients": ["patient", "patients", "case", "cases", "subject", "subjects", "individual", "individuals"],
    "Participants": ["participant", "participants", "attendee", "attendees", "respondent", "respondents"],
    "Inclusion Criteria": ["inclusion", "eligibility criteria", "study inclusion", "included"],
    "Exclusion Criteria": ["exclusion", "not eligible", "study exclusion", "excluded"],
    "Study Types": [
        "Case Report", "Case Series", "Cross-sectional Study", "Case-Control Study", "Cohort Study", "Randomized Controlled Clinical Trial",
        "Non-Randomized Controlled Trial", "Pilot Study", "Feasibility Study", "Longitudinal Study", "Retrospective Study", "Prospective Study",
        "Observational Study", "Experimental Study", "Interventional Study", "Descriptive Study", "Analytical Study", "Quasi-Experimental Study",
        "Epidemiological Study", "Ecological Study", "Systematic Review", "Meta-Analysis", "Mixed-Methods Study", "Narrative Review", "Scoping Review",
        "Rapid Review", "Umbrella Review", "Diagnostic Accuracy Study", "Validation Study", "Genome-Wide Association Study (GWAS)",
        "Gene-Environment Interaction Study", "Linkage Study", "Sensitivity/Specificity Study", "Cost-Effectiveness Study", "Health Technology Assessment",
        "Quality Improvement Study", "Translational Research", "Implementation Science Study", "Psychometric Study", "Community-Based Participatory Research (CBPR)",
        "In Vitro Study", "In Vivo Study", "Simulation Study", "Phenomenological Study", "Ethnographic Study", "Grounded Theory Study", "Narrative Study",
        "Case Study", "Pragmatic Trial", "Cluster Randomized Trial", "Adaptive Trial", "Phase 1 Clinical Trial", "Phase 2 Clinical Trial", "Phase 3 Clinical Trial",
        "Phase 4 Clinical Trial", "Real-World Evidence Study", "Comparative Effectiveness Study", "Proof-of-Concept Study", "Dose-Response Study", "Cross-Over Study",
        "Nested Study", "Multicenter Study", "Delphi Study", "Pragmatic Clinical Trial", "Registry-Based Study", "Historical Cohort Study",
        "Nested Case-Control Study", " double-blind ", "double blind", "placebo-controlled", "placebo controlled"
    ],
    "Co-morbidities": ["comorbidities", "co-morbidities", "comor-bidities", " comorbidities ", "comorbidities"],
    "Country": ["Afghanistan", "Australia", "Brazil", "Canada", "China", "France", "Germany", "India", "Japan", "Mexico", "Nigeria", "Russia",
                "South Africa", "United Kingdom", "United States", "Prefer Not to Answer"],
    "Race/Ethnicity": ["white", "Black", "African American", "Asian", "Native Hawaiian", "Other Pacific Islander", "American Indian",
                       "Alaska Native", "Other Race", "Two or More Races", "Hispanic", "latino", "Not Hispanic or latino"],
    "Follow-Up": ["years", "year", "weeks", "week", "months", "month", "days", "day"],
    "Remark":[
    "displayed", "exhibited", "revealed", "indicated", "illustrated",  "Showed",
    "noticed", "perceived", "detected", "discerned", "identified",   "Observed",
    "progress", "enhancement", "advancement", "growth", "betterment", "Improvement",
    "proved", "exhibited", "showcased", "conveyed", "validated",  "Demonstrated",
    "similar", "equivalent", "parallel", "analogous", "akin",  "Comparable",
    "more secure", "less risky", "protected", "shielded", "guarded",  "Safer",
    "chosen", "picked", "opted", "designated", "elected", "Selected"],
    "Intervention Groups": [
        "intervention grorup", "intervention groups", "treatment groups", "treatment group", "control groups", "control group", "placebo group", 
        "placebo groups"
    ]

}

# Regex patterns
numeric_regex = re.compile(r"\b(?:-?\d+\.?\d*%?|\d+-\d+%?|\d+(?: \d+)*%?)\b")
exclude_brackets_regex = re.compile(r"[$$($$]\s*[\d,/-]+\s*[$$)$$]")
date_regex = re.compile(r"\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b \d{1,2}, \d{4})\b", re.IGNORECASE)
table_regex = re.compile(r"^(?:\s*\d+\s+)+$")

# Build regex patterns for exact matches
gender_regex = re.compile(rf'\b(?:{"|".join(map(re.escape, keywords["Gender"]))})\b', re.IGNORECASE)
age_regex = re.compile(rf'\b(?:{"|".join(map(re.escape, keywords["Age"]))})\b', re.IGNORECASE)

# Time duration regex pattern
follow_up = re.compile(
    rf'\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:{"|".join(map(re.escape, keywords["Follow-Up"]))})(?:\b|s\b|-| to \d+)\b',
    re.IGNORECASE
)

# Author name regex pattern
author_pattern = r'\b(?:[A-Z]\.\s*)*[A-Z][a-zA-Z\.\-\']+(?:\s[A-Z][a-zA-Z\.\-\']+)*\b(?:\s[0-9]+)?'

# Words and patterns to exclude
exclude_words = {
    "Aim", "This", "the", "Article", "School", "Topical", "with", "compress",
    "Research", "Capsi", "India", "Australia", "and", "others", "January", "February",
    "March", "April", "May", "June", "July", "August", "September", "October", 
    "November", "December", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", 
    "Saturday", "Sunday", "AM", "PM", "University", "College", "Institute", "School",
    "of", "in", "on", "at", "by", "for", "with", "about", "against", "between", 
    "into", "through", "during", "before", "after", "above", "below", "to", "from",
    "up", "down", "in", "out", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
    "don", "should", "now", "Ginger", "Migraine"
}

# Key section markers to look for
key_sections = [
    "Summary", "Overview", "Synopsis", "Digest", "Outline", "Precis", "Recap",
    "Highlights", "Brief", "Introduction", "Executive Summary", "Abstract", 
    "A B S T R A C T", "Background",
    "Summary:", "Overview:", "Synopsis:", "Digest:", "Outline:", "Precis:", "Recap:",
    "Highlights:", "Brief:", "Introduction:", "Executive Summary:", "Abstract:", 
    "A B S T R A C T:", "Background:", "Objective", "Objective.", "Objective:", "A R T I C L E I N F O", "S U M M A R Y", "To cite this article:",
    "Copyright","Backgorund."
]