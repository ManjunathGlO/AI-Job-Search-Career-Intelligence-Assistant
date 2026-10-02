def format_digest(top_jobs, follow_ups):
    lines = ["AI JOB SEARCH ASSISTANT — DAILY DIGEST", ""]
    lines.append("TOP MATCHES")
    if not top_jobs:
        lines.append("No jobs currently meet the configured match threshold.")
    for i, j in enumerate(top_jobs, 1):
        lines.append(f"{i}. {j['title']} — {j['company']} | {j['location']} | Match {j['match']}%")
        if j.get("matched_skills"):
            lines.append(f"   Skills: {', '.join(j['matched_skills'][:6])}")
        if j.get("url"):
            lines.append(f"   {j['url']}")
    lines.append("")
    lines.append("FOLLOW-UPS DUE")
    if not follow_ups:
        lines.append("None.")
    for item in follow_ups:
        lines.append(f"- {item['title']} — {item['company']} | {item['status']} | applied {item.get('applied_date') or 'date not set'}")
        if item.get("url"):
            lines.append(f"  {item['url']}")
    return "\n".join(lines)
