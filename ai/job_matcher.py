import re

def match_job(description, profile):
    text = (description or "").lower()
    skills = profile["skills"]
    matched = [s for s in skills if re.search(r"\b" + re.escape(s.lower()) + r"\b", text)]
    missing = [s for s in skills if s not in matched]
    score = round((len(matched) / max(len(skills),1)) * 100)
    if not text:
        score = 0
    summary = (
        f"The description explicitly mentions {len(matched)} of your {len(skills)} tracked skills. "
        "This is a keyword-based screening aid, not a hiring prediction."
    )
    return {"score": score, "matched": matched, "missing": missing, "summary": summary}
