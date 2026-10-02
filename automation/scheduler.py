from apscheduler.schedulers.blocking import BlockingScheduler
from automation.pipeline import run_daily_pipeline
from config.settings_manager import load_settings
from notifications.notifier import send_email


def run():
    settings = load_settings()
    result = run_daily_pipeline()
    print(result["digest_text"])
    if settings.get("notifications_enabled"):
        send_email(result["digest_text"])


def main():
    settings = load_settings()
    scheduler = BlockingScheduler()
    scheduler.add_job(run, "cron", hour=int(settings["daily_run_hour"]), minute=int(settings["daily_run_minute"]), id="daily_job_pipeline", replace_existing=True)
    print(f"Stage 7 scheduler active: daily at {int(settings['daily_run_hour']):02d}:{int(settings['daily_run_minute']):02d} local machine time.")
    run()
    scheduler.start()


if __name__ == "__main__":
    main()
