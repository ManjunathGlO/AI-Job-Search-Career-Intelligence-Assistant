# Stage 7 Automation

The Stage 7 automation layer can run configured **authorized/public** JSON, RSS/Atom, or CSV feeds, deduplicate listings, store them in SQLite, calculate profile match scores, build a digest, and identify follow-ups due.

## Run scheduler

```bash
python -m automation.scheduler
```

The scheduler uses the configured local machine time. Keep the machine/process running.

## Source policy

Only add feeds/APIs/exports that you are authorized to access. The adapter intentionally does not authenticate to job boards, bypass CAPTCHAs, defeat robots rules, or submit applications.
