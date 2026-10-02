import hashlib
import re
from datetime import datetime

REQUIRED = ["title", "company", "location", "url", "description"]

def normalize_job(raw):
    raw = {str(k).strip().lower(): v for k, v in raw.items()}
    title = str(raw.get("title") or raw.get("job_title") or "").strip()
    company = str(raw.get("company") or raw.get("company_name") or "").strip()
    location = str(raw.get("location") or "").strip()
    url = str(raw.get("url") or raw.get("job_url") or raw.get("link") or "").strip()
    description = str(raw.get("description") or raw.get("job_description") or raw.get("summary") or "").strip()

    return {
        "title": re.sub(r"\s+", " ", title),
        "company": re.sub(r"\s+", " ", company),
        "location": re.sub(r"\s+", " ", location),
        "url": url,
        "description": re.sub(r"\s+", " ", description),
        "source": str(raw.get("source") or "Imported"),
    }

def fingerprint(job):
    # URL is strongest; otherwise use normalized title/company/location.
    basis = job["url"].strip().lower()
    if not basis:
        basis = "|".join([
            job["title"].lower(),
            job["company"].lower(),
            job["location"].lower()
        ])
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]

def validate_job(job):
    return bool(job["title"] and job["company"] and (job["url"] or job["description"]))

def deduplicate(jobs):
    seen = set()
    result = []
    for job in jobs:
        job = normalize_job(job)
        if not validate_job(job):
            continue
        fp = fingerprint(job)
        if fp not in seen:
            seen.add(fp)
            job["fingerprint"] = fp
            job["collected_at"] = datetime.now().isoformat(timespec="seconds")
            result.append(job)
    return result
