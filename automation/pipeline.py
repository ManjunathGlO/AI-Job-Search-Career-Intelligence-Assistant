from datetime import datetime, date
from database.database import init_db, add_job, job_exists, get_jobs
from jobs.collector import deduplicate
from jobs.source_adapters import fetch_sources
from profile.profile_manager import load_profile
from ai.semantic_matcher import semantic_match
from config.settings_manager import load_settings
from notifications.digest_formatter import format_digest


def ingest_jobs(raw_jobs, source="Authorized Feed"):
    init_db()
    jobs = deduplicate(raw_jobs)
    added = duplicates = 0
    for job in jobs:
        if job_exists(job["fingerprint"]):
            duplicates += 1
            continue
        if add_job(job["title"], job["company"], job["location"], job["url"],
                   job["description"], job.get("source") or source, job["fingerprint"], job.get("collected_at")):
            added += 1
    return {"received": len(raw_jobs), "valid_unique": len(jobs), "added": added, "duplicates": duplicates}


def collect_configured_sources():
    settings = load_settings()
    source_results = fetch_sources(settings.get("sources", []))
    summary = {"sources": [], "received": 0, "added": 0, "duplicates": 0, "errors": 0}
    for item in source_results:
        entry = {k: item.get(k) for k in ("source", "url", "count", "ok", "error")}
        if item.get("ok"):
            ing = ingest_jobs(item.get("jobs", []), item.get("source", "Public Feed"))
            entry.update(ing)
            summary["received"] += ing["received"]
            summary["added"] += ing["added"]
            summary["duplicates"] += ing["duplicates"]
        else:
            summary["errors"] += 1
        summary["sources"].append(entry)
    return summary


def build_ranked_digest(limit=None):
    init_db(); settings = load_settings(); profile = load_profile()
    limit = limit or settings["digest_limit"]
    minimum = settings["minimum_match_for_digest"]
    results = []
    for r in get_jobs():
        text = " ".join([str(r[1]), str(r[2]), str(r[3]), str(r[5])])
        m = semantic_match(text, profile)
        if m["score"] >= minimum:
            results.append({
                "id": r[0], "title": r[1], "company": r[2], "location": r[3],
                "url": r[4], "status": r[6], "found_date": r[7],
                "match": m["score"], "matched_skills": m["matched_skills"]
            })
    results.sort(key=lambda x: (x["match"], x["found_date"] or ""), reverse=True)
    return results[:limit]


def follow_up_candidates(days=None):
    init_db(); settings = load_settings()
    default_days = int(days or settings["follow_up_after_days"])
    today = date.today()
    out = []
    for r in get_jobs():
        status = r[6]
        applied_date = r[12]
        next_followup = r[18]
        if status not in ("Applied", "Assessment", "Interview", "Follow-up"):
            continue
        due = bool(next_followup and next_followup <= today.isoformat())
        if not next_followup and applied_date:
            try:
                due = (today - date.fromisoformat(applied_date)).days >= default_days
            except ValueError:
                due = False
        if due:
            out.append({
                "id": r[0], "title": r[1], "company": r[2], "status": status,
                "applied_date": applied_date, "next_followup_date": next_followup, "url": r[4]
            })
    return out


def run_daily_pipeline(raw_jobs=None, source="Authorized Feed", collect_sources=True):
    result = {"run_at": datetime.now().isoformat(timespec="seconds")}
    if raw_jobs is not None:
        result["ingestion"] = ingest_jobs(raw_jobs, source)
    elif collect_sources:
        result["source_collection"] = collect_configured_sources()
    top = build_ranked_digest()
    follow = follow_up_candidates()
    result["top_jobs"] = top
    result["follow_ups"] = follow
    result["digest_text"] = format_digest(top, follow)
    return result
