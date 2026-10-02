import streamlit as st
import pandas as pd
import re
from datetime import date, datetime, timedelta

from database.database import (
    init_db, add_job, job_exists, get_jobs, get_job, update_status,
    add_application_note, set_next_followup, update_feed_state, get_feed_state_counts
)
from jobs.importers import import_csv, import_excel
from jobs.collector import normalize_job, fingerprint, validate_job
from ai.job_analyzer import ai_analyze
from ai.message_generator import generate_message, MESSAGE_TYPES
from ai.job_capture import extract_job
from ai.semantic_matcher import semantic_match
from profile.profile_manager import load_profile, save_profile
from profile.resume_parser import extract_resume_text
from reports.daily_digest import build_digest
from config.settings_manager import load_settings, save_settings
from automation.pipeline import run_daily_pipeline, follow_up_candidates
from analytics.weekly import weekly_stats
from analytics.career_intelligence import application_funnel, skill_market, skill_gaps, recent_activity, followups_due
from analytics.export_tools import build_backup_zip
from integrations_portals import portal_searches, linkedin_jobs_url, naukri_search_url
from smart_feed import build_smart_feed, profile_feed_defaults

st.set_page_config(page_title="AI Job Search Assistant", page_icon="🤖", layout="wide")


def normalize_job_url(value):
    """Return a browser-safe absolute HTTP(S) URL or an empty string."""
    url = str(value or "").strip()
    if not url:
        return ""
    # Clean common copy/paste artifacts.
    url = url.strip().strip('<>\"\'')
    if url.startswith("//"):
        url = "https:" + url
    elif not re.match(r"^https?://", url, flags=re.I):
        # Stored job links occasionally arrive without a scheme.
        url = "https://" + url.lstrip("/")
    return url if re.match(r"^https?://[^\s]+$", url, flags=re.I) else ""
init_db()

profile = load_profile()
settings = load_settings()
STATUSES = ["Saved", "Analyzed", "Applied", "Assessment", "Interview", "Offer", "Rejected", "Follow-up"]
COLS = ["id", "title", "company", "location", "url", "description", "status", "found_date", "notes", "source", "fingerprint", "collected_at", "applied_date", "assessment_date", "interview_date", "offer_date", "rejected_date", "last_followup_date", "next_followup_date", "updated_at", "feed_state"]
rows = get_jobs()
df = pd.DataFrame(rows, columns=COLS) if rows else pd.DataFrame(columns=COLS)

st.title("🤖 AI Job Search & Application Assistant")
st.caption("Final v1.1 • Career intelligence + smart discovery + AI capture + application workspace")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Tracked", len(df))
c2.metric("Saved", int((df.status == "Saved").sum()) if len(df) else 0)
c3.metric("Applied", int((df.status == "Applied").sum()) if len(df) else 0)
c4.metric("Interviews", int((df.status == "Interview").sum()) if len(df) else 0)
c5.metric("Offers", int((df.status == "Offer").sum()) if len(df) else 0)
c6.metric("Follow-ups due", len(follow_up_candidates()))

tabs = st.tabs(["📥 Import", "🤖 AI Job Capture", "🎯 Smart Job Feed", "🧰 Application Workspace", "🎯 Match Jobs", "🧠 AI Analyze", "✉️ Messages", "📋 Tracker", "👤 My Profile", "🔗 Job Portals", "📅 Daily Digest", "⚙️ Automation", "📈 Analytics", "🏆 Career Intelligence"])

with tabs[0]:
    st.subheader("Import jobs")
    upload = st.file_uploader("CSV or Excel job feed/export", type=["csv", "xlsx"], key="import_jobs_upload")
    if upload:
        imported = import_csv(upload) if upload.name.lower().endswith(".csv") else import_excel(upload)
        st.write(f"Unique valid listings in this file: **{len(imported)}**")
        if imported:
            st.dataframe(pd.DataFrame(imported)[["title", "company", "location", "url", "source"]], use_container_width=True)
        if st.button("Import unique jobs", type="primary", key="import_unique_jobs"):
            added = dup = 0
            for job in imported:
                if job_exists(job["fingerprint"]):
                    dup += 1
                else:
                    add_job(job["title"], job["company"], job["location"], job["url"], job["description"], job.get("source", "Imported"), job["fingerprint"], job.get("collected_at"))
                    added += 1
            st.success(f"Added {added}; skipped {dup} duplicates.")
            st.rerun()

    st.divider(); st.subheader("Manual job")
    with st.form("manual"):
        title = st.text_input("Job title", key="manual_job_title")
        company = st.text_input("Company", key="manual_job_company")
        location = st.text_input("Location", key="manual_job_location")
        url = st.text_input("URL", key="manual_job_url")
        desc = st.text_area("Description", height=160, key="manual_job_description")
        if st.form_submit_button("Add"):
            j = normalize_job({"title": title, "company": company, "location": location, "url": url, "description": desc, "source": "Manual"})
            if not validate_job(j): st.error("Title + company + URL/description required.")
            elif job_exists(fingerprint(j)): st.warning("Already tracked.")
            else:
                add_job(j["title"], j["company"], j["location"], j["url"], j["description"], "Manual", fingerprint(j))
                st.success("Added."); st.rerun()



def safe_date(value, default=None):
    """Convert SQLite/string/date/datetime values to a date safely."""
    if value is None or value == "":
        return default
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return default
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            try:
                return datetime.fromisoformat(raw).date()
            except ValueError:
                return default
    return default


def choose_job(widget_key="choose_job_selectbox"):
    if not len(df):
        return None
    options = {f"{r.title} — {r.company} (#{r.id})": int(r.id) for r in df.itertuples()}
    choice = st.selectbox("Choose a job", list(options), key=widget_key)
    return df[df.id == options[choice]].iloc[0]

with tabs[1]:
    st.subheader("🤖 AI Job Capture")
    st.caption("Open a LinkedIn/Naukri job, copy the visible job details, paste them here, review the extracted fields, then save it to your tracker.")

    cap_source = st.selectbox("Source", ["LinkedIn", "Naukri", "Company careers", "Other"], key="capture_source")
    cap_url = st.text_input("Job URL (optional)", placeholder="Paste the job URL here", key="capture_url")
    cap_text = st.text_area(
        "Paste job details / description",
        height=330,
        placeholder="Copy the visible job title, company, location, requirements and description from the job page and paste it here...",
        key="capture_text",
    )

    if st.button("🤖 Extract job with AI", type="primary", key="capture_extract"):
        if len(cap_text.strip()) < 40:
            st.error("Paste more job details first (at least a few lines of the job posting).")
        else:
            with st.spinner("Extracting job details..."):
                captured, engine = extract_job(cap_text, cap_url, cap_source, profile)
            st.session_state["captured_job"] = captured
            st.session_state["captured_engine"] = engine
            st.success(f"Extraction complete • Engine: {engine}")

    captured = st.session_state.get("captured_job")
    if captured:
        st.divider()
        st.markdown("### Review before saving")
        engine = st.session_state.get("captured_engine", "local")
        st.caption(f"Captured with: {engine}")
        cc1, cc2 = st.columns(2)
        with cc1:
            captured["title"] = st.text_input("Job title", captured.get("title", ""), key="captured_title")
            captured["company"] = st.text_input("Company", captured.get("company", ""), key="captured_company")
            captured["location"] = st.text_input("Location", captured.get("location", ""), key="captured_location")
            captured["url"] = st.text_input("URL", captured.get("url", ""), key="captured_job_url")
        with cc2:
            captured["experience_requirement"] = st.text_input("Experience", captured.get("experience_requirement", "Not stated"), key="captured_experience")
            captured["education_requirement"] = st.text_input("Education", captured.get("education_requirement", "Not stated"), key="captured_education")
            captured["employment_type"] = st.text_input("Employment type", captured.get("employment_type", "Not stated"), key="captured_employment")
            captured["salary"] = st.text_input("Salary (if stated)", captured.get("salary", "Not stated"), key="captured_salary")
        captured["skills"] = st.text_input("Skills detected", ", ".join(captured.get("skills", [])), key="captured_skills")
        captured["description"] = st.text_area("Job description", captured.get("description", ""), height=240, key="captured_description")

        if captured.get("title") and captured.get("company"):
            match_text = " ".join([
                captured.get("title", ""), captured.get("company", ""), captured.get("location", ""),
                captured.get("description", ""), captured.get("skills", "") if isinstance(captured.get("skills"), str) else " ".join(captured.get("skills", []))
            ])
            cap_match = semantic_match(match_text, profile)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Profile match", f'{cap_match["score"]}%')
            m2.metric("Skills", f'{cap_match["skill_score"]}%')
            m3.metric("Role", f'{cap_match["role_score"]}%')
            m4.metric("Location", f'{cap_match["location_score"]}%')
            st.write("**Matched skills:**", ", ".join(cap_match["matched_skills"]) or "None")

        # Keep editable capture state in a plain dict before saving.
        save_source = cap_source
        if st.button("💾 Save captured job", type="primary", key="save_captured_job"):
            skills_list = captured.get("skills", [])
            if isinstance(skills_list, str):
                skills_list = [x.strip() for x in skills_list.split(",") if x.strip()]
            normalized = normalize_job({
                "title": captured.get("title", ""),
                "company": captured.get("company", ""),
                "location": captured.get("location", ""),
                "url": captured.get("url", ""),
                "description": captured.get("description", ""),
                "source": save_source,
            })
            if not validate_job(normalized):
                st.error("Title + company + URL/description are required.")
            elif job_exists(fingerprint(normalized)):
                st.warning("This job is already tracked. No duplicate was created.")
            else:
                add_job(normalized["title"], normalized["company"], normalized["location"], normalized["url"], normalized["description"], save_source, fingerprint(normalized))
                st.success("Job saved successfully. Open 🎯 Match Jobs or ✉️ Messages to continue.")
                st.session_state.pop("captured_job", None)
                st.rerun()

with tabs[2]:
    st.subheader("🎯 Smart Job Feed")
    st.caption("Profile-driven recommendations from jobs already in your tracker. The score is profile evidence, not a hiring prediction.")

    feed_defaults = profile_feed_defaults(profile)
    f1, f2 = st.columns(2)
    with f1:
        feed_roles = st.text_input("Target roles", ", ".join(feed_defaults["roles"]), key="feed_roles")
        feed_locations = st.text_input("Preferred locations", ", ".join(feed_defaults["locations"]), key="feed_locations")
        feed_keywords = st.text_input("Important keywords", ", ".join(feed_defaults["keywords"]), key="feed_keywords")
    with f2:
        feed_min = st.slider("Minimum match score", 0, 100, int(feed_defaults["min_score"]), key="feed_min_score")
        feed_search = st.text_input("Search within tracked jobs", feed_defaults["search"], key="feed_search")
        feed_sources = st.text_input("Sources (optional)", ", ".join(feed_defaults["sources"]), key="feed_sources")
        include_ignored = st.checkbox("Include ignored jobs", value=feed_defaults["include_ignored"], key="feed_include_ignored")

    prefs = {
        "roles": [x.strip() for x in feed_roles.split(",") if x.strip()],
        "locations": [x.strip() for x in feed_locations.split(",") if x.strip()],
        "keywords": [x.strip() for x in feed_keywords.split(",") if x.strip()],
        "min_score": int(feed_min),
        "sources": [x.strip() for x in feed_sources.split(",") if x.strip()],
        "search": feed_search.strip(),
        "include_ignored": bool(include_ignored),
    }
    if st.button("💾 Save feed preferences", type="primary", key="save_feed_preferences"):
        profile["job_feed"] = prefs
        save_profile(profile)
        st.success("Smart feed preferences saved.")

    feed_rows = [dict(zip(COLS, row)) for row in rows]
    ranked = build_smart_feed(feed_rows, profile, prefs)
    counts = get_feed_state_counts()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tracked jobs", len(df))
    k2.metric("New", counts.get("New", 0))
    k3.metric("Strong matches", sum(1 for x in ranked if x["score"] >= max(80, int(feed_min))))
    k4.metric("Ignored", counts.get("Ignored", 0))

    if not ranked:
        st.info("No jobs match these preferences. Lower the minimum score, broaden the filters, or import/capture more jobs.")
    else:
        st.markdown("### 🔥 Recommended jobs")
        for item in ranked[:25]:
            with st.container(border=True):
                top1, top2 = st.columns([5, 1])
                with top1:
                    st.markdown(f"### {item['title']}")
                    st.write(f"**{item['company']}** • {item.get('location') or 'Location not stated'}")
                    st.caption(f"{item.get('source') or 'Unknown source'} • Found {item.get('found_date') or '—'} • {item.get('feed_state') or 'New'}")
                with top2:
                    st.metric("Match", f"{item['score']}%")
                a, b, c, d = st.columns(4)
                a.write("**Skills**")
                a.write(", ".join(item["matched_skills"][:8]) or "None")
                b.write("**Role**")
                b.write(", ".join(item["matched_roles"]) or "No exact role")
                c.write("**Location**")
                c.write(", ".join(item["matched_locations"]) or "No exact location")
                d.write("**Quality**")
                d.write(", ".join(item["quality_flags"]) if item["quality_flags"] else "Looks complete")
                st.caption(f"Skill coverage: {item.get('skill_coverage', 0)}% • Evidence: {', '.join(item.get('evidence_terms', [])) or '—'}")
                x1, x2, x3, x4 = st.columns(4)
                job_url = normalize_job_url(item.get("url"))
                if job_url:
                    x1.link_button("🔗 Open job", job_url, type="primary", use_container_width=True)
                    x1.markdown(f"[Open in browser ↗]({job_url})")
                else:
                    x1.warning("No valid job URL")
                if x2.button("⭐ Save", key=f"feed_save_{item['id']}"):
                    update_feed_state(int(item["id"]), "Saved"); st.rerun()
                if x3.button("❌ Ignore", key=f"feed_ignore_{item['id']}"):
                    update_feed_state(int(item["id"]), "Ignored"); st.rerun()
                if x4.button("🆕 Mark new", key=f"feed_new_{item['id']}"):
                    update_feed_state(int(item["id"]), "New"); st.rerun()

    st.divider()
    st.markdown("### 🔄 Refresh configured public feeds")
    if st.button("Refresh feeds and rebuild recommendations", key="refresh_smart_feed"):
        with st.spinner("Collecting configured feeds..."):
            result = run_daily_pipeline()
        collection = result.get("source_collection", {})
        st.success(f"Refresh complete • {collection.get('added', 0)} new jobs added • {collection.get('duplicates', 0)} duplicates skipped • {collection.get('errors', 0)} source errors.")
        st.rerun()

with tabs[3]:
    st.subheader("🧰 Application Workspace")
    st.caption("One screen for a job's fit, evidence, application materials, status, follow-up and destination URL.")
    if len(df):
        workspace_options = {f"{r.title} — {r.company} (#{r.id})": int(r.id) for r in df.itertuples()}
        ws_choice = st.selectbox("Choose a job", list(workspace_options), key="workspace_job_select")
        ws_id = workspace_options[ws_choice]
        row = df[df.id == ws_id].iloc[0]
        job_text = " ".join([str(row.title), str(row.company), str(row.location), str(row.description)])
        match = semantic_match(job_text, profile)

        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Profile match", f'{match["score"]}%')
        h2.metric("Skills", f'{match["skill_score"]}%')
        h3.metric("Role", f'{match["role_score"]}%')
        h4.metric("Location", f'{match["location_score"]}%')

        left, right = st.columns([1.25, 1])
        with left:
            st.markdown(f"### {row.title}")
            st.write(f"**{row.company}** • {row.location or 'Location not stated'}")
            st.caption(f"{row.source or 'Unknown source'} • Found {row.found_date or '—'} • Status: {row.status}")
            st.markdown("#### 🎯 Why this matches")
            st.write("**Matched skills:**", ", ".join(match["matched_skills"]) or "None detected")
            st.write("**Matched roles:**", ", ".join(match["matched_roles"]) or "None detected")
            st.write("**Matched locations:**", ", ".join(match["matched_locations"]) or "None detected")
            st.write("**Shared evidence:**", ", ".join(match["shared_terms"][:15]) or "None detected")
            st.caption("This is a transparent profile-evidence score, not a hiring or interview prediction.")
            st.markdown("#### 📄 Job description")
            st.text_area("Job description", str(row.description or "No description stored."), height=260, disabled=True, key=f"workspace_desc_{ws_id}")
        with right:
            st.markdown("#### 📋 Application")
            ws_status = st.selectbox("Status", STATUSES, index=STATUSES.index(row.status) if row.status in STATUSES else 0, key=f"workspace_status_{ws_id}")
            follow_default = safe_date(row.next_followup_date, date.today() + timedelta(days=7))
            ws_follow = st.date_input("Next follow-up", value=follow_default, key=f"workspace_follow_{ws_id}")
            if st.button("💾 Save application status", type="primary", key=f"workspace_save_status_{ws_id}"):
                follow_days = max(0, (ws_follow - date.today()).days) if ws_status in ("Applied", "Assessment", "Interview") else None
                update_status(ws_id, ws_status, follow_days=follow_days)
                if ws_status not in ("Applied", "Assessment", "Interview"):
                    set_next_followup(ws_id, ws_follow.isoformat())
                st.success("Application updated.")
                st.rerun()

            job_url = normalize_job_url(row.url)
            if job_url:
                st.link_button("🔗 Open job", job_url, type="primary", use_container_width=True)
                st.markdown(f"[Open destination ↗]({job_url})")
            else:
                st.warning("No valid job URL is stored. Add the real job URL in Import or AI Job Capture.")

            st.markdown("#### ✉️ Application materials")
            ws_job = {"title": row.title, "company": row.company, "location": row.location, "url": row.url, "description": row.description}
            ws_store = st.session_state.setdefault("messages", {})
            for material_type in MESSAGE_TYPES:
                key = (ws_id, material_type)
                if st.button(f"✨ Generate {material_type}", key=f"workspace_gen_{ws_id}_{re.sub(r'[^a-zA-Z0-9]+', '_', material_type)}", use_container_width=True):
                    with st.spinner(f"Generating {material_type}..."):
                        ws_store[key] = generate_message(ws_job, profile, material_type)
                if ws_store.get(key):
                    st.text_area(material_type, ws_store[key], height=140 if material_type != "Cover letter" else 230, key=f"workspace_draft_{ws_id}_{re.sub(r'[^a-zA-Z0-9]+', '_', material_type)}")

            st.markdown("#### 📌 Follow-up note")
            ws_note = st.text_area("Add a note", height=90, key=f"workspace_note_{ws_id}")
            if st.button("Add note", key=f"workspace_add_note_{ws_id}"):
                if ws_note.strip():
                    add_application_note(ws_id, ws_note.strip())
                    st.success("Note added.")
                    st.rerun()
    else:
        st.info("Import or capture a job first.")

with tabs[4]:
    st.subheader("🎯 Resume-aware matching")
    if len(df):
        matches = []
        for r in df.itertuples():
            text = " ".join([str(r.title), str(r.company), str(r.location), str(r.description)])
            m = semantic_match(text, profile)
            matches.append({"ID": r.id, "Job": r.title, "Company": r.company, "Location": r.location, "Match": m["score"], "Matched skills": ", ".join(m["matched_skills"][:6]), "URL": r.url})
        mdf = pd.DataFrame(matches).sort_values("Match", ascending=False)
        st.dataframe(mdf[["ID", "Job", "Company", "Location", "Match", "Matched skills"]], use_container_width=True)
        st.caption("Match is a transparent profile-evidence score, not a prediction of hiring or interview probability.")
        selected_id = st.selectbox("Inspect job ID", mdf["ID"].tolist(), key="inspect_job_id")
        row = df[df.id == selected_id].iloc[0]
        full = semantic_match(" ".join([str(row.title), str(row.company), str(row.location), str(row.description)]), profile)
        a, b, c, d = st.columns(4)
        a.metric("Overall", f'{full["score"]}%'); b.metric("Skills", f'{full["skill_score"]}%'); c.metric("Role", f'{full["role_score"]}%'); d.metric("Location", f'{full["location_score"]}%')
        st.write("**Matched skills:**", ", ".join(full["matched_skills"]) or "None")
        st.write("**Matched roles:**", ", ".join(full["matched_roles"]) or "None")
        st.write("**Matched locations:**", ", ".join(full["matched_locations"]) or "None")
    else:
        st.info("Import or add jobs first.")

with tabs[5]:
    st.subheader("🧠 AI job analysis")
    row = choose_job("analyze_choose_job")
    if row is not None:
        if st.button("Analyze selected job", type="primary", key="analyze_selected_job"):
            result, source = ai_analyze(row.description, profile)
            st.session_state["analysis"] = result; st.session_state["analysis_source"] = source
            update_status(int(row.id), "Analyzed")
        result = st.session_state.get("analysis")
        if result:
            st.success("Engine: " + str(st.session_state.get("analysis_source")))
            st.write("### Summary"); st.write(result.get("summary", ""))
            st.write("**Matched:**", ", ".join(result.get("matched_skills", [])) or "None")
            st.write("**Missing / not detected:**", ", ".join(result.get("missing_skills", [])) or "None")
            st.write("**Experience:**", result.get("experience_requirement", "Not stated"))
            st.write("**Education:**", result.get("education_requirement", "Not stated"))
            st.write("**Location:**", result.get("location_requirement", "Not stated"))
            st.write("### Application notes")
            for n in result.get("application_notes", []): st.write("•", n)

with tabs[6]:
    st.subheader("✉️ Tailored application material")
    st.caption("Generate each material type independently. Cover letters are full-length letters; LinkedIn connection messages stay short.")
    row = choose_job("message_choose_job")
    if row is not None:
        job = {"title": row.title, "company": row.company, "location": row.location, "url": row.url, "description": row.description}
        job_key = int(row.id)
        selected_type = st.selectbox("Generate", MESSAGE_TYPES, key="message_type")
        action1, action2 = st.columns(2)
        if action1.button("✨ Generate selected", type="primary", key="generate_selected_message"):
            with st.spinner(f"Generating {selected_type}..."):
                draft = generate_message(job, profile, selected_type)
            st.session_state.setdefault("messages", {})[(job_key, selected_type)] = draft
        if action2.button("🚀 Generate all 4", key="generate_all_messages"):
            with st.spinner("Generating recruiter, referral, LinkedIn and cover letter drafts..."):
                store = st.session_state.setdefault("messages", {})
                for material_type in MESSAGE_TYPES:
                    store[(job_key, material_type)] = generate_message(job, profile, material_type)
            st.success("All four drafts generated.")

        st.divider()
        store = st.session_state.get("messages", {})
        for material_type in MESSAGE_TYPES:
            draft = store.get((job_key, material_type), "")
            if draft:
                st.markdown(f"### {material_type}")
                st.text_area(material_type, draft, height=300 if material_type == "Cover letter" else 180, key=f"draft_{job_key}_{re.sub(r'[^a-zA-Z0-9]+', '_', material_type)}")
            else:
                st.caption(f"{material_type}: not generated yet.")
        st.caption("Review every claim before sending. The assistant does not submit applications automatically.")

with tabs[7]:
    st.subheader("Application tracker")
    st.caption("Stage 7 records real application/interview dates and calculates follow-up due dates.")
    for r in df.itertuples():
        with st.container(border=True):
            a, b, c = st.columns([3, 2, 2])
            a.markdown(f"**{r.title}**  \n{r.company} • {r.location}  \n`{r.source}`")
            ns = b.selectbox("Status", STATUSES, index=STATUSES.index(r.status) if r.status in STATUSES else 0, key=f"s{r.id}")
            if ns != r.status:
                update_status(int(r.id), ns, settings["follow_up_after_days"]); st.rerun()
            c.write(f"Found: {r.found_date or '—'}")
            if r.applied_date: c.write(f"Applied: {r.applied_date}")
            if r.interview_date: c.write(f"Interview: {r.interview_date}")
            if r.next_followup_date: c.write(f"Follow-up: {r.next_followup_date}")
            if r.url: st.link_button("Open job", r.url)
            d, e = st.columns([2, 2])
            follow_default = safe_date(
                r.next_followup_date,
                date.today() + timedelta(days=int(settings["follow_up_after_days"]))
            )
            new_follow = d.date_input(
                "Next follow-up",
                value=follow_default,
                key=f"followup_date_{r.id}"
            )
            if d.button("Save date", key=f"fd{r.id}"):
                set_next_followup(int(r.id), new_follow.isoformat()); st.success("Follow-up date saved.")
            note = e.text_input("Add note", key=f"n{r.id}")
            if e.button("Save note", key=f"b{r.id}") and note:
                add_application_note(int(r.id), note); st.success("Saved")

with tabs[8]:
    st.subheader("👤 My profile")
    resume = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt", "md"], key="resume_upload")
    if resume and st.button("Extract resume", key="extract_resume"):
        text = extract_resume_text(resume); profile["resume_text"] = text; st.session_state["resume_preview"] = text; save_profile(profile); st.success("Resume text saved.")
    if st.session_state.get("resume_preview"): st.text_area("Extracted resume text", st.session_state["resume_preview"], height=220, key="resume_preview_text")
    st.divider()
    name = st.text_input("Name", profile.get("name", ""), key="profile_name"); roles = st.text_input("Target roles (comma separated)", ", ".join(profile.get("target_roles", [])), key="profile_roles")
    skills = st.text_area("Skills (comma separated)", ", ".join(profile.get("skills", [])), key="profile_skills"); locations = st.text_input("Preferred locations (comma separated)", ", ".join(profile.get("locations", [])), key="profile_locations")
    level = st.text_input("Experience level", profile.get("level", "Entry Level"), key="profile_level"); summary = st.text_area("Professional summary", profile.get("summary", ""), height=120, key="profile_summary"); projects = st.text_area("Projects (one per line)", "\n".join(profile.get("projects", [])), height=120, key="profile_projects")
    if st.button("Save profile", type="primary", key="save_profile"):
        profile.update({"name": name, "target_roles": [x.strip() for x in roles.split(",") if x.strip()], "skills": [x.strip() for x in skills.split(",") if x.strip()], "locations": [x.strip() for x in locations.split(",") if x.strip()], "level": level, "summary": summary, "projects": [x.strip() for x in projects.splitlines() if x.strip()]})
        save_profile(profile); st.success("Profile saved."); st.rerun()

with tabs[9]:
    st.subheader("🔗 LinkedIn & Naukri Job Portals")
    st.info("Stage 8 does not log into, scrape, or auto-apply on LinkedIn/Naukri. Use these one-click searches, then import an authorized export/feed into 📥 Import.")

    portal_profile = load_profile()
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("### LinkedIn Jobs")
        role = st.text_input("Role / keywords", ", ".join(portal_profile.get("target_roles", [])[:3]), key="portal_linkedin_role")
        loc = st.text_input("Location", ", ".join(portal_profile.get("locations", [])[:3]), key="portal_linkedin_location")
        posted = st.selectbox("Posted", ["24h", "week", "month", "any"], index=1, key="portal_linkedin_posted")
        if st.button("🔎 Open LinkedIn search", key="open_linkedin_search"):
            url = linkedin_jobs_url(role, loc, date_posted=None if posted == "any" else posted)
            st.link_button("Open LinkedIn Jobs", url)
            st.code(url)
    with p2:
        st.markdown("### Naukri Jobs")
        nrole = st.text_input("Role / keywords", ", ".join(portal_profile.get("target_roles", [])[:3]), key="portal_naukri_role")
        nloc = st.text_input("Location", ", ".join(portal_profile.get("locations", [])[:3]), key="portal_naukri_location")
        if st.button("🔎 Open Naukri search", key="open_naukri_search"):
            url = naukri_search_url(nrole, nloc)
            st.link_button("Open Naukri Jobs", url)
            st.code(url)

    st.divider()
    st.markdown("### 🔄 Generate all searches from your profile")
    searches = portal_searches(portal_profile, date_posted="week")
    if searches:
        sdf = pd.DataFrame(searches)
        st.dataframe(sdf[["portal", "role", "location"]], use_container_width=True)
        for i, item in enumerate(searches[:12]):
            st.link_button(f"{item['portal']}: {item['role']} — {item['location']}", item["url"], key=f"portal_link_{i}")

    st.divider()
    st.markdown("### 📥 How jobs enter your assistant")
    st.markdown("1. Open a LinkedIn/Naukri search above.  2. Review jobs yourself.  3. Use an authorized export/feed if your account or integration provides one.  4. Import the CSV/Excel file in **📥 Import**.  5. The normal deduplication, matching, digest and tracker pipeline takes over.")

with tabs[10]:
    st.subheader("📅 Daily job digest")
    if st.button("Build today's digest", type="primary", key="build_daily_digest"):
        digest = build_digest(); st.metric("Jobs reviewed", digest["total_jobs"])
        top = digest["top_jobs"]
        if top:
            digest_df = pd.DataFrame([{"Match": j["score"], "Job": j["title"], "Company": j["company"], "Location": j["location"], "Matched skills": ", ".join(j["matched_skills"][:5])} for j in top])
            st.dataframe(digest_df, use_container_width=True)
            st.download_button("Download digest CSV", digest_df.to_csv(index=False), file_name="daily_job_digest.csv", mime="text/csv")
        else: st.info("No jobs available.")
    due = follow_up_candidates()
    if due:
        st.warning(f"{len(due)} follow-up(s) are due.")
        st.dataframe(pd.DataFrame(due), use_container_width=True)

with tabs[11]:
    st.subheader("⚙️ Automation control center")
    h = st.number_input("Daily run hour", 0, 23, int(settings["daily_run_hour"]), key="daily_run_hour"); minute = st.number_input("Daily run minute", 0, 59, int(settings["daily_run_minute"]), key="daily_run_minute")
    limit = st.number_input("Digest size", 1, 50, int(settings["digest_limit"]), key="digest_size"); minmatch = st.slider("Minimum profile-match score", 0, 100, int(settings["minimum_match_for_digest"]), key="minimum_match_score")
    days = st.number_input("Default follow-up after days", 1, 60, int(settings["follow_up_after_days"]), key="follow_up_days"); notify = st.checkbox("Enable email notification", value=bool(settings["notifications_enabled"]), key="enable_email_notifications")
    if st.button("Save automation settings", type="primary", key="save_automation_settings"):
        settings.update({"daily_run_hour": int(h), "daily_run_minute": int(minute), "digest_limit": int(limit), "minimum_match_for_digest": int(minmatch), "follow_up_after_days": int(days), "notifications_enabled": notify}); save_settings(settings); st.success("Automation settings saved.")

    st.divider(); st.subheader("🌐 Job sources")
    st.caption("Use public/authorized feeds and APIs. This app does not log into sites, bypass CAPTCHAs, or scrape restricted pages.")
    sources = settings.get("sources", [])
    if sources:
        for i, source in enumerate(sources):
            with st.container(border=True):
                x, y, z = st.columns([2, 5, 1])
                provider_label = str(source.get("provider", "generic")).title()
                x.markdown(f"**{source.get('name', 'Unnamed')}**\n\n`{provider_label}`")
                y.write(source.get("url") or source.get("board_token") or source.get("site") or "")
                if st.button("Remove", key=f"remove_source_{i}"):
                    sources.pop(i); settings["sources"] = sources; save_settings(settings); st.rerun()
    else:
        st.info("No automatic job sources configured yet. Add a Greenhouse/Lever board or a generic feed below.")

    with st.form("source_form"):
        provider = st.selectbox("Source type", ["Greenhouse public board", "Lever public postings", "Generic JSON/RSS/CSV"], key="source_provider")
        sname = st.text_input("Source name", placeholder="Company careers", key="source_name")
        if provider == "Greenhouse public board":
            token = st.text_input("Greenhouse board token", placeholder="e.g. companyname", key="greenhouse_token")
            company = st.text_input("Company name", placeholder="Company", key="greenhouse_company")
            if st.form_submit_button("Add Greenhouse source"):
                if not sname or not token: st.error("Source name and board token are required.")
                else:
                    sources.append({"name": sname, "provider": "greenhouse", "board_token": token.strip(), "company": company.strip(), "enabled": True})
                    settings["sources"] = sources; save_settings(settings); st.success("Greenhouse source saved."); st.rerun()
        elif provider == "Lever public postings":
            site = st.text_input("Lever site/company slug", placeholder="e.g. leverdemo", key="lever_site")
            company = st.text_input("Company name", placeholder="Company", key="lever_company")
            if st.form_submit_button("Add Lever source"):
                if not sname or not site: st.error("Source name and site slug are required.")
                else:
                    sources.append({"name": sname, "provider": "lever", "site": site.strip(), "company": company.strip(), "enabled": True})
                    settings["sources"] = sources; save_settings(settings); st.success("Lever source saved."); st.rerun()
        else:
            surl = st.text_input("Feed URL", placeholder="https://example.com/jobs.json", key="source_url")
            sformat = st.selectbox("Format", ["auto", "json", "rss", "csv"], key="source_format")
            if st.form_submit_button("Add generic source"):
                if not sname or not surl: st.error("Name and URL are required.")
                else:
                    sources.append({"name": sname, "provider": "generic", "url": surl.strip(), "format": sformat, "enabled": True}); settings["sources"] = sources; save_settings(settings); st.success("Source saved."); st.rerun()

    st.divider()
    if st.button("🧪 Test configured sources", key="test_sources"):
        from jobs.source_adapters import fetch_sources
        with st.spinner("Testing job sources..."):
            test_results = fetch_sources(settings.get("sources", []))
        for item in test_results:
            if item.get("ok"):
                st.success(f"{item['source']}: {item['count']} jobs received")
            else:
                st.error(f"{item['source']}: {item.get('error', 'Unknown error')}")

    if st.button("▶ Run Stage 8 pipeline now", type="primary", key="run_stage7_pipeline"):
        with st.spinner("Collecting configured feeds and ranking jobs..."):
            result = run_daily_pipeline()
        st.success("Pipeline completed.")
        if result.get("source_collection"): st.json(result["source_collection"])
        st.text_area("Digest preview", result["digest_text"], height=350, key="pipeline_digest_preview")
        st.download_button("Download digest", result["digest_text"], file_name="ai_job_daily_digest.txt")

with tabs[12]:
    st.subheader("📈 Weekly job-search analytics")
    stats = weekly_stats()

    # KPI cards
    a, b, c, d = st.columns(4)
    a.metric("Jobs added (7 days)", stats["jobs_added"])
    b.metric("Total applied", stats["total_applied"])
    c.metric("Total interviews", stats["total_interviews"])
    d.metric("Total offers", stats["total_offers"])

    st.divider()

    # Status breakdown
    st.markdown("### 📌 Application status")
    status_items = stats.get("statuses", {})
    status_df = pd.DataFrame(
        list(status_items.items()),
        columns=["Status", "Jobs"]
    )
    if status_df.empty:
        st.info("No jobs have been tracked yet.")
    else:
        status_df = status_df.sort_values("Jobs", ascending=False).reset_index(drop=True)
        left, right = st.columns([1, 1.4])
        with left:
            st.dataframe(status_df, use_container_width=True, hide_index=True)
        with right:
            st.bar_chart(status_df.set_index("Status")["Jobs"], height=280)

    st.divider()

    # Recent companies and locations
    col_company, col_location = st.columns(2)

    with col_company:
        st.markdown("### 🏢 Top companies — last 7 days")
        company_df = pd.DataFrame(
            stats.get("top_companies", []),
            columns=["Company", "Jobs"]
        )
        if company_df.empty:
            st.info("No recent jobs found.")
        else:
            st.dataframe(company_df, use_container_width=True, hide_index=True)
            st.bar_chart(company_df.set_index("Company")["Jobs"], height=280)

    with col_location:
        st.markdown("### 📍 Top locations — last 7 days")
        location_df = pd.DataFrame(
            stats.get("top_locations", []),
            columns=["Location", "Jobs"]
        )
        if location_df.empty:
            st.info("No recent locations found.")
        else:
            st.dataframe(location_df, use_container_width=True, hide_index=True)
            st.bar_chart(location_df.set_index("Location")["Jobs"], height=280)

    st.caption("Analytics summarize your tracked job-search activity. They do not predict hiring outcomes.")


with tabs[13]:
    st.subheader("🏆 Career Intelligence")
    st.caption("Final-stage command center for application performance, market skills, profile gaps and backup/export. Scores describe your tracked evidence; they do not predict hiring outcomes.")

    jobs_for_intel = [dict(zip(COLS, row)) for row in rows]
    funnel = application_funnel(jobs_for_intel)

    st.markdown("### 📊 Application funnel")
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    f1.metric("Tracked", funnel["tracked"])
    f2.metric("Applied", funnel["applied"])
    f3.metric("Responses", funnel["responses"])
    f4.metric("Interviews", funnel["interviews"])
    f5.metric("Offers", funnel["offers"])
    f6.metric("Rejected", funnel["rejected"])
    r1, r2, r3 = st.columns(3)
    r1.metric("Response rate", f'{funnel["response_rate"]}%')
    r2.metric("Interview rate", f'{funnel["interview_rate"]}%')
    r3.metric("Offer rate", f'{funnel["offer_rate"]}%')

    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("### 🔥 Job-market skills in your tracked jobs")
        market = skill_market(jobs_for_intel)
        if market:
            mdf = pd.DataFrame(market[:15], columns=["Skill", "Job mentions"])
            st.dataframe(mdf, use_container_width=True, hide_index=True)
            st.bar_chart(mdf.set_index("Skill")["Job mentions"], height=320)
        else:
            st.info("Collect more job descriptions to build a market-skill view.")
    with right:
        st.markdown("### 🧩 Profile skill gaps")
        gaps = skill_gaps(profile, jobs_for_intel)
        if gaps:
            gdf = pd.DataFrame(gaps, columns=["Skill to consider", "Job mentions"])
            st.dataframe(gdf, use_container_width=True, hide_index=True)
            st.caption("These are skills appearing in your tracked jobs that are not listed in your current profile. Review them before adding anything to your resume.")
        else:
            st.success("No tracked-market gaps detected from the current skill vocabulary.")

    st.divider()
    st.markdown("### 📌 Action center")
    due = followups_due(jobs_for_intel)
    recent = recent_activity(jobs_for_intel, days=30)
    a1, a2, a3 = st.columns(3)
    a1.metric("Follow-ups due", len(due))
    a2.metric("Applications — last 30 days", sum(1 for j in recent if j.get("applied_date")))
    a3.metric("New jobs — last 30 days", len(recent))
    if due:
        due_df = pd.DataFrame([{
            "ID": j["id"], "Job": j["title"], "Company": j["company"],
            "Status": j["status"], "Follow-up": j["next_followup_date"]
        } for j in due])
        st.dataframe(due_df, use_container_width=True, hide_index=True)
    else:
        st.success("No follow-ups are currently due.")

    st.divider()
    st.markdown("### 📦 Export & backup")
    export_df = pd.DataFrame(jobs_for_intel)
    if not export_df.empty:
        st.download_button("⬇️ Download all jobs CSV", export_df.to_csv(index=False), file_name="ai_job_search_jobs.csv", mime="text/csv", key="final_jobs_csv")
    backup = build_backup_zip(rows, COLS, profile, settings)
    st.download_button("🛡️ Download complete project data backup", backup, file_name="ai_job_search_backup.zip", mime="application/zip", key="final_backup")

    st.divider()
    st.markdown("### ✅ Final workflow")
    st.markdown("**Discover → Capture → Match → Analyze → Generate application material → Apply manually → Track → Follow up → Measure → Improve.**")
    st.caption("The assistant does not automatically submit applications, log into job portals, bypass CAPTCHAs, or bypass access controls.")
