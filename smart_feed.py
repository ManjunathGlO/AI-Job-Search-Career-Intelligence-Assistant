from datetime import date, datetime, timedelta
import re
from ai.semantic_matcher import semantic_match


def _tokens(value):
    return set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.&/-]{1,}", str(value or "").lower()))


def _text(row):
    return " ".join(str(row.get(k, "") or "") for k in ("title", "company", "location", "description", "source"))


def quality_flags(row):
    flags = []
    if not str(row.get("title", "")).strip(): flags.append("Missing title")
    if not str(row.get("company", "")).strip(): flags.append("Missing company")
    if not str(row.get("description", "")).strip(): flags.append("Missing description")
    if not str(row.get("url", "")).strip(): flags.append("Missing URL")
    found = str(row.get("found_date", "") or "")[:10]
    if found:
        try:
            age = (date.today() - date.fromisoformat(found)).days
            if age > 60: flags.append("Older than 60 days")
        except ValueError:
            pass
    title = str(row.get("title", "")).lower()
    if any(x in title for x in ("intern", "internship")) and "intern" not in " ".join(row.get("target_roles", [])).lower():
        flags.append("Internship")
    return flags


def build_smart_feed(rows, profile, prefs):
    roles = [x.strip() for x in prefs.get("roles", []) if x.strip()]
    locations = [x.strip() for x in prefs.get("locations", []) if x.strip()]
    keywords = [x.strip() for x in prefs.get("keywords", []) if x.strip()]
    sources = [x.strip().lower() for x in prefs.get("sources", []) if x.strip()]
    min_score = int(prefs.get("min_score", 60))
    search = str(prefs.get("search", "")).strip().lower()
    include_ignored = bool(prefs.get("include_ignored", False))

    results = []
    for row in rows:
        item = dict(row)
        if item.get("feed_state") == "Ignored" and not include_ignored:
            continue
        if sources and str(item.get("source", "")).lower() not in sources:
            continue

        text = _text(item)
        low = text.lower()
        if search and search not in low:
            continue
        if roles and not any(r.lower() in low for r in roles):
            continue
        if locations and not any(l.lower() in low for l in locations):
            continue
        if keywords and not any(k.lower() in low for k in keywords):
            continue

        match = semantic_match(text, profile)
        item.update({
            "score": int(match["score"]),
            "matched_skills": match["matched_skills"],
            "matched_roles": match["matched_roles"],
            "matched_locations": match["matched_locations"],
            "quality_flags": quality_flags(item),
            "skill_coverage": round((len(match["matched_skills"]) / max(1, len(profile.get("skills", [])))) * 100),
            "evidence_terms": match.get("shared_terms", [])[:12],
        })
        if item["score"] < min_score:
            continue
        results.append(item)

    results.sort(key=lambda x: (x["score"], x.get("found_date") or "", x.get("id", 0)), reverse=True)
    return results


def profile_feed_defaults(profile):
    saved = profile.get("job_feed", {}) or {}
    return {
        "roles": saved.get("roles") or profile.get("target_roles", []),
        "locations": saved.get("locations") or profile.get("locations", []),
        "keywords": saved.get("keywords") or profile.get("skills", [])[:8],
        "min_score": int(saved.get("min_score", 60)),
        "sources": saved.get("sources", []),
        "search": saved.get("search", ""),
        "include_ignored": bool(saved.get("include_ignored", False)),
    }
