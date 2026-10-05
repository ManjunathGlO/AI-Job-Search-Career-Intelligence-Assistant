# 🤖 AI Job Search & Career Intelligence Assistant

> **An end-to-end, local-first job intelligence platform for discovering, capturing, matching, analyzing, tracking, and improving a job search.**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-Local%20Database-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI%20Optional-412991?logo=openai&logoColor=white)](https://openai.com/)
[![Status](https://img.shields.io/badge/Status-Portfolio%20Ready-success)](#)

---

## 🎯 Why I Built This

Job searching is often fragmented across job portals, spreadsheets, resumes, messages, application trackers, and follow-up reminders.

This project brings those workflows into one application.

Instead of treating a job posting as just a URL, the system treats it as a structured data object that can be:

**discovered → captured → cleaned → matched → analyzed → acted on → tracked → measured → improved.**

The goal is not to automate away the candidate. The goal is to reduce repetitive work and give the candidate better information for each application decision.

---

## 🚀 Product Overview

```text
                    ┌──────────────────────┐
                    │  Job Sources/Portals │
                    │ CSV • Excel • Feeds  │
                    │ LinkedIn • Naukri    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Job Ingestion      │
                    │ Normalize • Validate │
                    │ Deduplicate          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   AI Job Capture     │
                    │ Structured extraction│
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
     ┌─────────────────┐               ┌─────────────────┐
     │ Resume / Profile│               │ Job Intelligence│
     │ Skills • Roles  │               │ Skills • Role   │
     │ Location • Level│               │ Location • Req. │
     └────────┬────────┘               └────────┬────────┘
              └────────────────┬────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Explainable Matching │
                    │ Score + Evidence     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Application Workspace│
                    │ Analyze • Draft •    │
                    │ Apply • Track        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Career Intelligence  │
                    │ Funnel • Skills •    │
                    │ Gaps • Analytics     │
                    └──────────────────────┘
```

---

## ⭐ Core Capabilities

### 1. 🤖 AI Job Capture

Paste visible job information from a job portal and convert unstructured text into structured job data.

Extracted fields can include:

- Job title
- Company
- Location
- Job URL
- Job description
- Skills
- Experience requirements
- Education
- Employment type
- Salary information when present
- Source

The extracted record can be reviewed before it is saved.

---

### 2. 🎯 Resume-Aware Job Matching

The matching engine compares a job against the candidate profile and resume.

The score is designed as a **transparent profile-fit indicator**, not a hiring probability.

Matching evidence can include:

- Skill overlap
- Role alignment
- Location alignment
- Shared terminology/evidence
- Skill coverage

Example:

```text
🎯 Match Score: 82/100

Skills           52/60
Role             18/20
Location          8/10
Shared Evidence   4/10

Matched:
✓ SQL
✓ Excel
✓ Power BI
✓ Python

Potential gaps:
• Tableau
• Advanced statistics
```

This makes the score interpretable instead of presenting an unexplained number.

---

### 3. 🔎 Smart Job Feed

The Smart Job Feed turns the stored job database into a personalized shortlist.

Users can filter jobs by:

- Target role
- Location
- Keywords
- Minimum match score
- Source
- Job state

Supported actions include:

- ⭐ Save
- ❌ Ignore
- 🆕 Mark New
- 🔗 Open Job
- 🤖 Analyze
- 📋 Track

---

### 4. 🧰 Application Workspace

The Application Workspace consolidates the most important information for one job.

```text
Job
 ├── Match score
 ├── Matching evidence
 ├── Job details
 ├── Application status
 ├── Follow-up
 ├── Notes
 ├── Open Job
 └── Application materials
       ├── Recruiter message
       ├── Referral request
       ├── LinkedIn connection
       └── Cover letter
```

This reduces the need to move between multiple screens while preparing an application.

---

### 5. ✉️ Four Independent Application Drafts

The application assistant generates four distinct types of content:

| Output | Purpose |
|---|---|
| 👤 Recruiter Message | Short professional outreach |
| 🤝 Referral Request | Ask a contact for guidance/referral |
| 🔗 LinkedIn Connection | Concise connection request |
| 📄 Cover Letter | Longer job-specific application draft |

AI-generated content is intended as a draft for human review.

---

### 6. 🧠 AI Job Analysis

Analyze a job description for:

- Role summary
- Required skills
- Missing skills
- Experience requirements
- Education requirements
- Important keywords
- Candidate-fit observations

The application supports local fallback behavior for supported workflows when an AI API key is not configured.

---

### 7. 📋 Application Lifecycle Tracking

Track the complete application journey:

```text
Saved
  ↓
Applied
  ↓
Assessment
  ↓
Interview
  ↓
Offer
```

Alternative outcomes can also be tracked, including rejection and follow-up activity.

The system records application and follow-up dates so the job search becomes measurable rather than spreadsheet-driven.

---

### 8. 📅 Daily Digest & Automation

The automation layer can:

- Collect configured public/authorized feeds
- Identify new jobs
- Deduplicate listings
- Rebuild recommendations
- Prepare daily digests
- Identify follow-up actions

Scheduling is designed for local, user-controlled operation.

---

### 9. 📊 Analytics

The analytics layer provides visibility into:

- Jobs added
- Application status breakdown
- Top companies
- Top locations
- Recent activity
- Weekly application activity

This allows the user to understand the behavior of their job search instead of relying only on memory.

---

### 10. 🏆 Career Intelligence

The final intelligence layer turns application history and job descriptions into career insights.

It provides:

#### Application Funnel

```text
Jobs Found
   ↓
Jobs Saved
   ↓
Applications
   ↓
Responses
   ↓
Interviews
   ↓
Offers
```

#### Job-Market Skill Frequency

Identifies skills that repeatedly appear across collected job descriptions.

#### Profile Skill Gaps

Compares the candidate's profile with skills observed in target jobs.

#### Follow-up Action Center

Highlights applications that may require attention.

#### Activity View

Provides a recent view of job-search activity.

#### Export & Backup

Supports jobs CSV export and project-data backup.

---

# 🏗️ Technical Architecture

```text
┌─────────────────────────────────────────────────────┐
│                    Streamlit UI                     │
│ app.py                                              │
└──────────────────────────┬──────────────────────────┘
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
       ▼                   ▼                    ▼
   Job Layer           AI Layer            Profile Layer
   ─────────           ────────            ─────────────
   Importers           Capture              Resume Parser
   Collector           Analyzer             Profile Manager
   Source Adapters     Matcher              Semantic Matcher
   Smart Feed          Messages
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
                    Database Layer
                    ───────────────
                    SQLite
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Automation Layer            Analytics Layer
       Scheduler/Pipeline          Weekly Analytics
       Daily Reports              Career Intelligence
       Notifications              Export/Backup
```

---

# 🛠️ Technology Stack

### Application

- **Python**
- **Streamlit**
- **SQLite**

### Data & Analysis

- **Pandas**
- Structured data normalization
- Deduplication
- Aggregation
- Skill-frequency analysis

### AI / NLP

- **OpenAI API — optional**
- Structured job extraction
- Job analysis
- Application-message generation
- Resume/job matching assistance
- Local fallback logic for supported workflows

### Document Processing

- **pypdf** — PDF resume extraction
- **python-docx** — DOCX resume extraction

### Automation & Integration

- **APScheduler**
- **Requests**
- Public/authorized JSON, RSS/Atom and CSV feeds
- Greenhouse/Lever public job-board adapters
- LinkedIn/Naukri assisted search

### Configuration

- `.env`
- JSON settings
- Local SQLite persistence

---

# 📁 Project Structure

```text
AI-Job-Search-Assistant/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── ai/
│   ├── job_analyzer.py
│   ├── job_capture.py
│   ├── job_matcher.py
│   ├── message_generator.py
│   └── semantic_matcher.py
│
├── analytics/
│   ├── career_intelligence.py
│   ├── export_tools.py
│   └── weekly.py
│
├── automation/
│   ├── daily_report.py
│   ├── pipeline.py
│   └── scheduler.py
│
├── config/
│   ├── settings.json
│   └── settings_manager.py
│
├── database/
│   └── database.py
│
├── jobs/
│   ├── collector.py
│   ├── importers.py
│   └── source_adapters.py
│
├── notifications/
│   ├── digest_formatter.py
│   └── notifier.py
│
├── profile/
│   ├── profile_manager.py
│   └── resume_parser.py
│
├── reports/
│   └── daily_digest.py
│
└── data/
    ├── .gitkeep
    └── sample_jobs.csv
```

---

# ⚙️ Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/<your-username>/AI-Job-Search-Assistant.git
cd AI-Job-Search-Assistant
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 4. Configure optional AI access

Copy:

```text
.env.example
```

to:

```text
.env
```

Add your API configuration if you want to enable the AI-powered workflows.

Do not commit `.env` or API keys to GitHub.

## 5. Start the application

```bash
python -m streamlit run app.py
```

Then open the local Streamlit URL shown in your terminal.

---

# 🔐 Responsible Access & Automation

This project intentionally uses a **human-in-the-loop** model.

It does **not**:

- Log into LinkedIn or Naukri
- Bypass CAPTCHAs
- Bypass paywalls
- Circumvent access controls
- Scrape restricted/private pages
- Automatically submit job applications

For LinkedIn/Naukri, the application provides assisted search and a user-controlled capture workflow.

For automated collection, the application is designed around public or authorized feeds such as supported Greenhouse/Lever boards and generic JSON/RSS/CSV sources.

The user reviews generated application material and submits applications manually.

---

# 🧪 Example Workflow

### Step 1 — Define the profile

Set:

```text
Target roles
Skills
Locations
Experience level
Education
Projects
Resume
```

### Step 2 — Find jobs

Use:

- Public job feeds
- CSV/Excel
- LinkedIn assisted search
- Naukri assisted search

### Step 3 — Capture a job

Paste visible job information into **AI Job Capture**.

### Step 4 — Review

Check the extracted:

- Title
- Company
- Location
- URL
- Skills
- Experience
- Description

### Step 5 — Match

Review the transparent profile-fit score.

### Step 6 — Prepare application

Generate:

- Recruiter message
- Referral request
- LinkedIn message
- Cover letter

### Step 7 — Apply manually

Open the original job posting and submit the application yourself.

### Step 8 — Track

Update:

```text
Saved → Applied → Assessment → Interview → Offer
```

### Step 9 — Measure

Use Career Intelligence to understand:

- Application volume
- Response rate
- Interview rate
- Job-market skills
- Profile gaps
- Follow-up actions

---

# 📈 What This Project Demonstrates

This project is intentionally broader than a CRUD application.

It demonstrates practical ability across:

### Data Analytics

- Data ingestion
- Cleaning
- Normalization
- Deduplication
- Filtering
- Aggregation
- KPI design
- Funnel analysis
- Skill-frequency analysis
- Data export

### Python Development

- Modular architecture
- SQLite persistence
- File processing
- API integration
- Scheduling
- Error handling
- Configuration management

### AI / Applied NLP

- Unstructured job-text extraction
- Job-description analysis
- Resume/job matching
- Explainable evidence
- AI-assisted content generation
- Local fallback strategies

### Product Thinking

- User workflow design
- Human-in-the-loop automation
- State management
- Application lifecycle tracking
- Action-oriented dashboards
- Reliability and edge-case handling

---

# 💡 Key Engineering Decisions

### Local-first architecture

Job and profile data can be stored locally, reducing dependency on a hosted backend for the core workflow.

### Explainable matching

The system exposes evidence behind a match score rather than presenting an opaque AI ranking.

### Modular design

Job ingestion, AI processing, profile management, analytics, automation, and notifications are separated into modules so individual components can evolve independently.

### Human-in-the-loop automation

Automation handles repetitive preparation and organization, while the user retains control over application submission.

### Fallback behavior

Supported AI workflows include local fallback behavior so the application remains useful when external AI access is unavailable.

---

# 🗺️ Development Evolution

The project was developed incrementally:

```text
Stage 1
MVP + SQLite
      ↓
Stage 2
AI Analysis + Messages
      ↓
Stage 3
Job Import + Deduplication
      ↓
Stage 4
Resume-Aware Matching
      ↓
Stage 5
Automation Foundation
      ↓
Stage 6
Notifications + Analytics
      ↓
Stage 7
Public Job Sources
      ↓
Stage 8
LinkedIn/Naukri Assisted Search
      ↓
Stage 9
AI Job Capture
      ↓
Stage 10
Smart Job Discovery
      ↓
Stage 12
Career Intelligence
      ↓
v1.1 / v1.1.1
Product Hardening + Application Workspace
```

---

# 🧭 Current Status

**Version:** `v1.1.1`

**Status:** Portfolio-ready / local production release

The current release includes the complete end-to-end workflow:

> **Discover → Capture → Analyze → Match → Generate → Apply → Track → Follow Up → Measure → Improve**

---

# 🔮 Future Scope

The current release is intentionally feature-complete. Potential future improvements could include:

- Hosted multi-user deployment
- Role-based authentication
- Cloud database
- More authorized job-board integrations
- Advanced semantic retrieval
- Improved resume tailoring
- Automated reporting to email
- More sophisticated experiment tracking for job-search strategies

These are intentionally outside the current local-first scope.

---

# 🎓 Portfolio Positioning

### Recommended project title

**AI Job Search & Career Intelligence Assistant**

### Resume-ready description

> Built a local-first AI job intelligence platform using Python, Streamlit, SQLite, Pandas, and optional OpenAI integration to capture and normalize job postings, match opportunities against resume/profile evidence, generate application drafts, track application lifecycles, automate follow-ups, and analyze job-market skill gaps.

### Short portfolio description

> **AI-powered job intelligence platform that transforms fragmented job-search activity into a structured workflow for discovery, matching, application tracking, and career insights.**

---

# 👨‍💻 Author

**Manjunath G L**

Data Analytics | Python | SQL | Power BI | AI | Automation

---

## 🚀 Let's Connect

<p align="center">
  <a href="https://www.linkedin.com/in/manjunathgl/" target="_blank">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"/>
  </a>
  <a href="https://github.com/ManjunathGlO" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/>
  </a>
  <a href="https://portfolio-chi-ruby-36.vercel.app/" target="_blank">
    <img src="https://img.shields.io/badge/Portfolio-Visit-1F4E79?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Portfolio"/>
  </a>
</p>

<p align="center">
  <b>📊 Turning Data into Insights • 🤖 Building Intelligent Solutions • 🚀 Creating Business Impact</b>
</p>

<p align="center">
  <i>Open to Data Analyst opportunities, collaborations, and meaningful projects.</i>
</p>

<p align="center">
  ⭐ If you find my projects useful, consider giving them a star!
</p>

<p align="center">
  <img src="https://komarev.com/ghpvc/?username=ManjunathGlO&style=flat-square&color=1F4E79" alt="Profile Views"/>
</p>

<p align="center">
  <sub>Built with curiosity, consistency, and a passion for data.</sub>
</p>

---

## ⭐ If You Found This Project Useful

Feel free to star the repository and explore the implementation.

> **Built to demonstrate how data, automation, and AI can solve a practical workflow problem end-to-end.**
