from collections import Counter
from datetime import date, timedelta
from database.database import get_jobs, init_db

def weekly_stats():
    init_db(); rows = get_jobs(); cutoff = (date.today() - timedelta(days=7)).isoformat()
    recent = [r for r in rows if (r[7] or "") >= cutoff]
    statuses = Counter(r[6] for r in rows)
    companies = Counter(r[2] for r in recent)
    locations = Counter(r[3] for r in recent if r[3])
    applied = [r for r in rows if r[12]]
    interviews = [r for r in rows if r[14]]
    offers = [r for r in rows if r[15]]
    return {
        "jobs_added": len(recent),
        "statuses": dict(statuses),
        "top_companies": companies.most_common(10),
        "top_locations": locations.most_common(10),
        "total_applied": len(applied),
        "total_interviews": len(interviews),
        "total_offers": len(offers),
    }
