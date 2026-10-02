from pathlib import Path
import io
import zipfile
from datetime import datetime
import pandas as pd


def jobs_dataframe(rows, columns):
    return pd.DataFrame(rows, columns=columns)


def build_backup_zip(rows, columns, profile, settings):
    jobs_df = jobs_dataframe(rows, columns)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("jobs.csv", jobs_df.to_csv(index=False))
        z.writestr("profile.json", __import__("json").dumps(profile, indent=2, ensure_ascii=False))
        z.writestr("settings.json", __import__("json").dumps(settings, indent=2, ensure_ascii=False))
        z.writestr("README.txt", "AI Job Search Assistant backup created " + datetime.now().isoformat(timespec="seconds"))
    return buf.getvalue()
