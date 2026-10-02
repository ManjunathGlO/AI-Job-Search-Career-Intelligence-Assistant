import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

DB = "data/jobs.db"


def connect():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB)


def init_db():
    con = connect()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        url TEXT,
        description TEXT,
        status TEXT DEFAULT 'Saved',
        found_date TEXT,
        notes TEXT DEFAULT '',
        source TEXT DEFAULT 'Manual',
        fingerprint TEXT,
        collected_at TEXT,
        applied_date TEXT,
        assessment_date TEXT,
        interview_date TEXT,
        offer_date TEXT,
        rejected_date TEXT,
        last_followup_date TEXT,
        next_followup_date TEXT,
        updated_at TEXT
    )""")

    cols = {r[1] for r in cur.execute("PRAGMA table_info(jobs)").fetchall()}
    migrations = {
        "source": "ALTER TABLE jobs ADD COLUMN source TEXT DEFAULT 'Manual'",
        "fingerprint": "ALTER TABLE jobs ADD COLUMN fingerprint TEXT",
        "collected_at": "ALTER TABLE jobs ADD COLUMN collected_at TEXT",
        "applied_date": "ALTER TABLE jobs ADD COLUMN applied_date TEXT",
        "assessment_date": "ALTER TABLE jobs ADD COLUMN assessment_date TEXT",
        "interview_date": "ALTER TABLE jobs ADD COLUMN interview_date TEXT",
        "offer_date": "ALTER TABLE jobs ADD COLUMN offer_date TEXT",
        "rejected_date": "ALTER TABLE jobs ADD COLUMN rejected_date TEXT",
        "last_followup_date": "ALTER TABLE jobs ADD COLUMN last_followup_date TEXT",
        "next_followup_date": "ALTER TABLE jobs ADD COLUMN next_followup_date TEXT",
        "updated_at": "ALTER TABLE jobs ADD COLUMN updated_at TEXT",
        "feed_state": "ALTER TABLE jobs ADD COLUMN feed_state TEXT DEFAULT 'New'",
    }
    for name, sql in migrations.items():
        if name not in cols:
            cur.execute(sql)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_fingerprint ON jobs(fingerprint)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_feed_state ON jobs(feed_state)")
    cur.execute("UPDATE jobs SET feed_state='New' WHERE feed_state IS NULL OR feed_state=''")
    con.commit()
    con.close()


def add_job(title, company, location, url, description, source="Manual", fingerprint=None, collected_at=None):
    now = datetime.now().isoformat(timespec="seconds")
    con = connect()
    try:
        con.execute(
            """INSERT INTO jobs(title,company,location,url,description,found_date,source,fingerprint,collected_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (title, company, location, url, description, date.today().isoformat(), source,
             fingerprint, collected_at or now, now)
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()


def job_exists(fingerprint_value):
    if not fingerprint_value:
        return False
    con = connect()
    row = con.execute("SELECT id FROM jobs WHERE fingerprint=?", (fingerprint_value,)).fetchone()
    con.close()
    return row is not None


def get_jobs():
    con = connect()
    rows = con.execute("""SELECT id,title,company,location,url,description,status,
                          found_date,notes,source,fingerprint,collected_at,applied_date,
                          assessment_date,interview_date,offer_date,rejected_date,
                          last_followup_date,next_followup_date,updated_at,feed_state
                          FROM jobs ORDER BY id DESC""").fetchall()
    con.close()
    return rows


def get_job(job_id):
    con = connect()
    row = con.execute("""SELECT id,title,company,location,url,description,status,
                          found_date,notes,source,fingerprint,collected_at,applied_date,
                          assessment_date,interview_date,offer_date,rejected_date,
                          last_followup_date,next_followup_date,updated_at,feed_state
                          FROM jobs WHERE id=?""", (job_id,)).fetchone()
    con.close()
    return row


def update_status(job_id, status, followup_days=None, follow_days=None):
    if followup_days is None:
        followup_days = follow_days
    today = date.today().isoformat()
    now = datetime.now().isoformat(timespec="seconds")
    field_by_status = {
        "Applied": "applied_date",
        "Assessment": "assessment_date",
        "Interview": "interview_date",
        "Offer": "offer_date",
        "Rejected": "rejected_date",
    }
    con = connect()
    if status in field_by_status:
        field = field_by_status[status]
        if followup_days is not None and status in ("Applied", "Assessment", "Interview"):
            next_date = (date.today() + timedelta(days=int(followup_days))).isoformat()
            con.execute(f"UPDATE jobs SET status=?, {field}=COALESCE({field},?), next_followup_date=?, updated_at=? WHERE id=?",
                        (status, today, next_date, now, job_id))
        else:
            con.execute(f"UPDATE jobs SET status=?, {field}=COALESCE({field},?), updated_at=? WHERE id=?",
                        (status, today, now, job_id))
    elif status == "Follow-up":
        con.execute("UPDATE jobs SET status=?, last_followup_date=?, next_followup_date=NULL, updated_at=? WHERE id=?",
                    (status, today, now, job_id))
    else:
        con.execute("UPDATE jobs SET status=?, updated_at=? WHERE id=?", (status, now, job_id))
    con.commit()
    con.close()


def set_next_followup(job_id, followup_date):
    con = connect()
    con.execute("UPDATE jobs SET next_followup_date=?, updated_at=? WHERE id=?",
                (followup_date, datetime.now().isoformat(timespec="seconds"), job_id))
    con.commit(); con.close()


def add_application_note(job_id, note):
    con = connect()
    con.execute("UPDATE jobs SET notes = CASE WHEN notes='' THEN ? ELSE notes || char(10) || ? END, updated_at=? WHERE id=?",
                (note, note, datetime.now().isoformat(timespec="seconds"), job_id))
    con.commit(); con.close()


def update_feed_state(job_id, feed_state):
    con = connect()
    con.execute("UPDATE jobs SET feed_state=?, updated_at=? WHERE id=?",
                (feed_state, datetime.now().isoformat(timespec="seconds"), job_id))
    con.commit(); con.close()


def get_feed_state_counts():
    con = connect()
    rows = con.execute("SELECT COALESCE(feed_state, 'New'), COUNT(*) FROM jobs GROUP BY COALESCE(feed_state, 'New')").fetchall()
    con.close()
    return dict(rows)
