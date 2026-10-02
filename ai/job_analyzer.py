import json
import os
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

def local_analyze(description, profile):
    text = (description or "").lower()
    skills = profile.get("skills", [])
    matched = [s for s in skills if re.search(r"\b" + re.escape(s.lower()) + r"\b", text)]
    missing = [s for s in skills if s.lower() not in text]
    experience = "Not detected"
    if re.search(r"\b(0|1)\s*(?:-|to)?\s*2?\s*years?\b", text) or "fresher" in text or "entry level" in text:
        experience = "Entry-level / early career language detected"
    elif re.search(r"\b[2-9]\+?\s*years?\b", text):
        experience = "Experience requirement detected; review exact wording"
    return {
        "summary": f"Detected {len(matched)} of {len(skills)} profile skills in the job description.",
        "matched_skills": matched,
        "missing_skills": missing,
        "experience_requirement": experience,
        "education_requirement": "Review job description",
        "location_requirement": "Review job description",
        "keywords": matched,
        "application_notes": [
            "Verify the exact experience and education requirements before applying.",
            "Use matched skills naturally in your resume or application answers."
        ]
    }

def ai_analyze(description, profile):
    key = os.getenv("OPENAI_API_KEY")
    if not key or OpenAI is None:
        return local_analyze(description, profile), "local"

    client = OpenAI(api_key=key)
    prompt = f"""
Analyze this job posting for a candidate.

Candidate profile:
{json.dumps(profile, indent=2)}

Job posting:
{description}

Return JSON only with these keys:
summary, matched_skills, missing_skills, experience_requirement,
education_requirement, location_requirement, keywords, application_notes.

Do not invent requirements. If something is not stated, say "Not stated".
"""
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-mini"),
        input=prompt
    )
    data = json.loads(response.output_text)
    return data, "openai"
