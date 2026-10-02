import json
import os
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

MESSAGE_TYPES = [
    "Recruiter message",
    "Referral request",
    "LinkedIn connection message",
    "Cover letter",
]


def _fallback(job, profile, message_type):
    name = profile.get("name", "") or "Candidate"
    company = job.get("company", "the company") or "the company"
    title = job.get("title", "the role") or "the role"
    skills = profile.get("skills", [])[:6]
    skill_text = ", ".join(skills) if skills else "SQL, Excel, Power BI and Python"

    if message_type == "Recruiter message":
        return (f"Hi, I came across the {title} opportunity at {company} and would like to be considered. "
                f"My background includes {skill_text}, and I’m actively building practical data analytics projects. "
                f"Could you please let me know if my profile is a fit for the role? Thank you.")
    if message_type == "Referral request":
        return (f"Hi, I noticed the {title} opening at {company}. I’m interested in applying and my background includes "
                f"{skill_text}. If you’re comfortable doing so, would you be willing to refer me or share any guidance on the role? "
                f"I’d really appreciate it. Thank you!")
    if message_type == "LinkedIn connection message":
        return (f"Hi, I’m {name}. I’m exploring opportunities in data analytics and came across the {title} role at {company}. "
                f"I’d be glad to connect and learn more about the team and opportunity. Thank you!")
    return (f"Dear Hiring Team,\n\nI am writing to express my interest in the {title} position at {company}. "
            f"My background includes {skill_text}, along with hands-on analytics projects involving data preparation, analysis and visualization. "
            f"I am particularly interested in applying these skills to practical business problems and continuing to grow in an analytics role.\n\n"
            f"I would welcome the opportunity to discuss how my background aligns with this position. Thank you for your consideration.\n\n"
            f"Sincerely,\n{name}")


def generate_message(job, profile, message_type="Recruiter message"):
    if message_type not in MESSAGE_TYPES:
        message_type = "Recruiter message"

    key = os.getenv("OPENAI_API_KEY")
    if key and OpenAI:
        client = OpenAI(api_key=key)
        prompt = f"""
Write ONLY the requested application material type: {message_type}.

Candidate:
{json.dumps(profile, indent=2)}

Job:
{json.dumps(job, indent=2)}

Requirements by type:
- Recruiter message: 70-120 words, concise professional outreach to a recruiter.
- Referral request: 70-120 words, polite request to an employee for a referral; do not pressure them.
- LinkedIn connection message: maximum 300 characters, natural and concise connection request.
- Cover letter: 250-400 words, professional letter with greeting, 2-3 focused paragraphs, and closing. Do not include a subject line.

General rules:
- Tailor the text to the specific job and company.
- Use only facts present in the candidate profile and job.
- Never invent experience, employers, achievements, certifications, or metrics.
- If the candidate is entry-level, present projects/skills honestly as projects or skills.
- Do not repeat the same generic text across different material types.
- Return plain text only.
"""
        try:
            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
                input=prompt,
            )
            result = (response.output_text or "").strip()
            if result:
                return result
        except Exception:
            pass

    return _fallback(job, profile, message_type)
