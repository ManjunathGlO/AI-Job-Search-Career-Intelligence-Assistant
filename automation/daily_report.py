from database.database import init_db, get_jobs
from collections import Counter

def daily_report():
    init_db()
    jobs = get_jobs()
    statuses = Counter(j[6] for j in jobs)
    return {
        "total_jobs": len(jobs),
        "statuses": dict(statuses),
        "follow_up": statuses.get("Follow-up", 0)
    }

if __name__ == "__main__":
    print(daily_report())
