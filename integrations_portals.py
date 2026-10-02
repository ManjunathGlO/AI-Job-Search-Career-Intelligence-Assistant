"""Job-portal helpers for Stage 8.

This module deliberately does not automate login, scraping, CAPTCHA solving,
or application submission on LinkedIn/Naukri. It generates user-facing search
links and supports importing an authorized export/feed into the normal pipeline.
"""
from urllib.parse import urlencode, quote_plus


def linkedin_jobs_url(keywords, location="", remote=False, date_posted=None):
    params = {"keywords": keywords.strip()}
    if location.strip():
        params["location"] = location.strip()
    if remote:
        params["f_WT"] = "2"
    if date_posted in {"24h", "week", "month"}:
        params["f_TPR"] = {"24h": "r86400", "week": "r604800", "month": "r2592000"}[date_posted]
    return "https://www.linkedin.com/jobs/search/?" + urlencode(params)


def _naukri_slug(value):
    import re
    value = value.strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def naukri_search_url(keywords, location=""):
    # Use Naukri's public SEO job-search route. The older /jobs-search?k=...
    # route can return 404, while the public job-search pages use slugs such
    # as /data-analyst-jobs-in-bangalore.
    role = _naukri_slug(keywords) or "jobs"
    loc = _naukri_slug(location) if location.strip() else ""
    # Naukri commonly uses Bangalore in SEO slugs even when the UI says Bengaluru.
    loc = loc.replace("bengaluru", "bangalore")
    path = f"{role}-jobs"
    if loc:
        path += f"-in-{loc}"
    return "https://www.naukri.com/" + path


def portal_searches(profile, date_posted="week"):
    roles = profile.get("target_roles") or ["Data Analyst"]
    locations = profile.get("locations") or [""]
    results = []
    for role in roles[:8]:
        for location in locations[:8]:
            results.append({
                "portal": "LinkedIn",
                "role": role,
                "location": location or "Any location",
                "url": linkedin_jobs_url(role, location, date_posted=date_posted),
            })
            results.append({
                "portal": "Naukri",
                "role": role,
                "location": location or "Any location",
                "url": naukri_search_url(role, location),
            })
    return results
