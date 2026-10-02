from datetime import date
from database.database import init_db, get_jobs
from profile.profile_manager import load_profile
from ai.semantic_matcher import semantic_match

def build_digest():
    init_db()
    profile = load_profile()
    rows = get_jobs()
    results = []
    for r in rows:
        job = {
            "id": r[0], "title": r[1], "company": r[2],
            "location": r[3], "url": r[4], "description": r[5]
        }
        m = semantic_match(
            " ".join([job["title"], job["company"], job["location"], job["description"]]),
            profile
        )
        results.append({**job, **m})
    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "date": date.today().isoformat(),
        "total_jobs": len(results),
        "top_jobs": results[:10]
    }
