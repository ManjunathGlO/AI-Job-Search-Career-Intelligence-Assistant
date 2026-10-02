import re
from collections import Counter
from datetime import date, datetime, timedelta

COMMON_SKILLS = [
    "SQL", "Excel", "Power BI", "Tableau", "Python", "Pandas", "NumPy",
    "DAX", "Power Query", "Statistics", "Machine Learning", "AWS", "Azure",
    "MySQL", "PostgreSQL", "R", "ETL", "Data Visualization", "Git", "AI",
    "Java", "JavaScript", "Spark", "Snowflake", "BigQuery", "Looker"
]


def _text(job):
    return " ".join(str(job.get(k) or "") for k in ("title", "company", "location", "description")).lower()


def application_funnel(jobs):
    total = len(jobs)
    applied = [j for j in jobs if j.get("applied_date") or j.get("status") in {"Applied", "Assessment", "Interview", "Offer", "Rejected", "Follow-up"}]
    responses = [j for j in jobs if j.get("assessment_date") or j.get("interview_date") or j.get("offer_date")]
    interviews = [j for j in jobs if j.get("interview_date") or j.get("status") in {"Interview", "Offer"}]
    offers = [j for j in jobs if j.get("offer_date") or j.get("status") == "Offer"]
    rejected = [j for j in jobs if j.get("rejected_date") or j.get("status") == "Rejected"]
    def pct(n, d): return round((n / d) * 100, 1) if d else 0.0
    return {
        "tracked": total, "applied": len(applied), "responses": len(responses),
        "interviews": len(interviews), "offers": len(offers), "rejected": len(rejected),
        "response_rate": pct(len(responses), len(applied)),
        "interview_rate": pct(len(interviews), len(applied)),
        "offer_rate": pct(len(offers), len(applied)),
    }


def skill_market(jobs, skills=None):
    skills = skills or COMMON_SKILLS
    corpus = "\n".join(_text(j) for j in jobs)
    counts = []
    for skill in skills:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        n = len(re.findall(pattern, corpus))
        if n:
            counts.append((skill, n))
    counts.sort(key=lambda x: (-x[1], x[0]))
    return counts


def skill_gaps(profile, jobs, limit=10):
    market = skill_market(jobs, profile.get("skills", []))
    if not market:
        market = skill_market(jobs)
    own = {str(x).strip().lower() for x in profile.get("skills", [])}
    gaps = [(skill, n) for skill, n in market if skill.lower() not in own]
    return gaps[:limit]


def recent_activity(jobs, days=30):
    cutoff = date.today() - timedelta(days=days)
    result = []
    for j in jobs:
        raw = j.get("applied_date") or j.get("found_date")
        try:
            d = date.fromisoformat(str(raw)[:10]) if raw else None
        except ValueError:
            d = None
        if d and d >= cutoff:
            result.append(j)
    return result


def followups_due(jobs):
    today = date.today()
    due = []
    for j in jobs:
        raw = j.get("next_followup_date")
        if not raw:
            continue
        try:
            d = date.fromisoformat(str(raw)[:10])
        except ValueError:
            continue
        if d <= today and j.get("status") not in {"Offer", "Rejected"}:
            due.append(j)
    return due
