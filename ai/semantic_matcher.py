import re

def _terms(text):
    return set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.&/-]{1,}", (text or "").lower()))

def semantic_match(job_text, profile):
    job = _terms(job_text)
    profile_text = " ".join([
        " ".join(profile.get("skills", [])),
        " ".join(profile.get("target_roles", [])),
        profile.get("summary", ""),
        " ".join(profile.get("projects", [])),
        profile.get("resume_text", "")
    ])
    prof = _terms(profile_text)

    overlap = sorted(job & prof)
    skill_matches = [s for s in profile.get("skills", []) if s.lower() in (job_text or "").lower()]
    role_matches = [r for r in profile.get("target_roles", []) if r.lower() in (job_text or "").lower()]
    location_matches = [l for l in profile.get("locations", []) if l.lower() in (job_text or "").lower()]

    # Transparent heuristic, deliberately not presented as hiring probability.
    skill_score = min(60, round(len(skill_matches) / max(1, len(profile.get("skills", []))) * 60))
    role_score = 20 if role_matches else 0
    location_score = 10 if location_matches else 0
    evidence_score = min(10, round(len(overlap) / 20 * 10))
    total = min(100, skill_score + role_score + location_score + evidence_score)

    return {
        "score": total,
        "skill_score": skill_score,
        "role_score": role_score,
        "location_score": location_score,
        "evidence_score": evidence_score,
        "matched_skills": skill_matches,
        "matched_roles": role_matches,
        "matched_locations": location_matches,
        "shared_terms": overlap[:30]
    }
