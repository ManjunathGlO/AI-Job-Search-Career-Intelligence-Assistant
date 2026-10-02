import json
from pathlib import Path

PATH = Path("config/settings.json")
DEFAULT = {
    "daily_run_hour": 8,
    "daily_run_minute": 0,
    "digest_limit": 10,
    "follow_up_after_days": 7,
    "minimum_match_for_digest": 50,
    "notifications_enabled": False,
    "sources": []
}


def load_settings():
    if PATH.exists():
        try:
            raw = json.loads(PATH.read_text(encoding="utf-8"))
            return {**DEFAULT, **raw, "sources": raw.get("sources", [])}
        except Exception:
            pass
    return DEFAULT.copy()


def save_settings(settings):
    PATH.parent.mkdir(exist_ok=True)
    PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
