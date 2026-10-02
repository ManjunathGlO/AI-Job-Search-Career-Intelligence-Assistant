import json
import os
import re
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _clean_json(text):
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _local_extract(text, url="", source="Other"):
    raw = (text or "").strip()
    lines = [re.sub(r"\s+", " ", x).strip() for x in raw.splitlines() if x.strip()]
    lower = raw.lower()

    title = ""
    company = ""
    location = ""
    experience = "Not stated"
    education = "Not stated"
    employment_type = "Not stated"
    salary = "Not stated"

    title_patterns = [r"(?:job title|role|position)\s*[:\-]\s*(.+)", r"^(.{3,80}(?:analyst|engineer|developer|manager|intern|associate|specialist|consultant).*)$"]
    for line in lines[:30]:
        for pat in title_patterns:
            m = re.search(pat, line, flags=re.I)
            if m:
                title = m.group(1).strip(); break
        if title: break

    for label, target in [("company", "company"), ("organization", "company"), ("employer", "company")]:
        m = re.search(rf"{label}\s*[:\-]\s*(.+)", raw, flags=re.I)
        if m:
            company = m.group(1).split("\n")[0].strip(); break
    if not company and len(lines) > 1:
        company = lines[1] if lines[0].lower() == title.lower() else ""

    m = re.search(r"(?:location|based in|job location)\s*[:\-]\s*(.+)", raw, flags=re.I)
    if m: location = m.group(1).split("\n")[0].strip()

    m = re.search(r"(?:\d+\s*(?:-|to)\s*\d+|\d+\+)\s*years?[^\n.]*", raw, flags=re.I)
    if m: experience = m.group(0).strip()
    elif re.search(r"\bfresher\b|\bentry[- ]level\b|\b0[- ]1\s*years?", lower): experience = "Entry-level / fresher"

    m = re.search(r"(?:bachelor|master|degree|diploma|b\.?tech|b\.?e\.?|m\.?tech|mba)[^\n.]*", raw, flags=re.I)
    if m: education = m.group(0).strip()

    for term in ["full-time", "part-time", "contract", "internship", "intern", "temporary"]:
        if term in lower:
            employment_type = term.title(); break

    m = re.search(r"(?:₹|rs\.?|inr|usd|\$)[\s\d,.-]+(?:lpa|per annum|year|month)?", raw, flags=re.I)
    if m: salary = m.group(0).strip()

    skill_vocab = [
        "SQL", "Excel", "Power BI", "Tableau", "Python", "Pandas", "NumPy", "DAX", "Power Query",
        "Machine Learning", "scikit-learn", "MySQL", "PostgreSQL", "AWS", "Azure", "GCP", "Java",
        "JavaScript", "React", "Django", "Git", "GitHub", "Data Visualization", "Statistics", "ETL",
        "PLC", "Automation", "Robotics", "IoT", "IIoT"
    ]
    skills = [s for s in skill_vocab if re.search(r"\b" + re.escape(s.lower()) + r"\b", lower)]

    description = raw
    return {
        "title": title or (lines[0] if lines else ""),
        "company": company,
        "location": location,
        "url": url.strip(),
        "description": description,
        "skills": skills,
        "experience_requirement": experience,
        "education_requirement": education,
        "employment_type": employment_type,
        "salary": salary,
        "source": source or "Other",
        "captured_at": datetime.now().isoformat(timespec="seconds"),
    }


def extract_job(text, url="", source="Other", profile=None):
    """Extract structured job fields with OpenAI when configured, otherwise use local heuristics."""
    key = os.getenv("OPENAI_API_KEY")
    if not key or OpenAI is None:
        return _local_extract(text, url, source), "local"

    client = OpenAI(api_key=key)
    prompt = f"""
Extract a job posting into JSON for a job-search assistant.

Candidate profile (use only for context, never invent job facts):
{json.dumps(profile or {}, indent=2)}

Source: {source}
URL supplied by user: {url}

Pasted job content:
{text}

Return JSON only with exactly these keys:
title, company, location, url, description, skills, experience_requirement,
education_requirement, employment_type, salary, source.

Rules:
- Extract only facts present in the pasted content.
- If a field is not stated, use an empty string or "Not stated".
- skills must be an array of concise skill names.
- Preserve the job description faithfully but remove obvious navigation noise when possible.
- Use the supplied URL unchanged.
- Use the supplied source unchanged.
"""
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
            input=prompt,
        )
        data = _clean_json(response.output_text)
        data.setdefault("url", url.strip())
        data.setdefault("source", source or "Other")
        data["captured_at"] = datetime.now().isoformat(timespec="seconds")
        data["skills"] = data.get("skills") or []
        return data, "openai"
    except Exception:
        # A capture workflow should remain usable if an API call fails.
        return _local_extract(text, url, source), "local fallback"
