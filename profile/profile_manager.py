import json
from pathlib import Path

PROFILE_FILE = Path("data/profile.json")

DEFAULT_PROFILE = {
    "name": "Candidate",
    "target_roles": ["Data Analyst", "Business Analyst", "BI Analyst", "Junior Data Analyst"],
    "skills": ["SQL", "Excel", "Power BI", "Python", "Pandas", "Tableau",
               "Data Visualization", "Machine Learning", "AI", "IIoT"],
    "locations": ["Bengaluru", "Hyderabad", "Pune", "Chennai", "Remote"],
    "level": "Entry Level",
    "education": [],
    "summary": "",
    "projects": [],
    "resume_text": ""
}

def load_profile():
    if PROFILE_FILE.exists():
        try:
            data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
            return {**DEFAULT_PROFILE, **data}
        except Exception:
            pass
    return DEFAULT_PROFILE.copy()

def save_profile(profile):
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
