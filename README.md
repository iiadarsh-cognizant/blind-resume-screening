# Blindspot — Bias-Free Blind Hiring Pipeline

> A privacy-first multi-agent system that ranks job candidates without ever exposing their identity to any LLM, using Neuro SAN's `sly_data` mechanism as a cryptographic-style privacy firewall.

---

## What it does

Blindspot automates the entire hiring screening process while guaranteeing that no candidate name, email, or personal identifier is ever seen by any AI model. The ranking is done purely on merit — skills, experience, education, certifications, and project count. Only after a human recruiter approves the top-N slice are identities revealed, and only for those approved candidates.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | Neuro SAN (`neuro-san-studio`) |
| LLM | Anthropic Claude (claude-sonnet-4-5) |
| Database | SQLite |
| Web backend | Flask |
| Frontend | Vanilla HTML/CSS/JS |
| Dataset | AI-Powered Resume Screening Dataset 2025 (Kaggle) |

---

## Project Structure

```
blind-resume-screening/
├── coded_tools/
│   ├── __init__.py                          # Critical — marks coded_tools as Python module
│   └── blindspot/
│       ├── __init__.py
│       ├── resume_anonymizer.py             # Seals identities into sly_data
│       ├── identity_resolver.py             # Reveals only top-N identities
│       └── availability_matcher.py          # Deterministic calendar matching
├── registries/
│   ├── aaosa.hocon                          
│   ├── blindspot.hocon                      # Agent network definition
│   ├── manifest.hocon                       # Agent registry
├── webapp/
│   ├── app.py                               # Flask backend — proxies to Neuro SAN
│   ├── requirements.txt
│   └── templates/
│       └── index.html                       # Full UI
├── config/
│   └── llm_config.hocon                     # LLM provider config
├── setup_database.py                        # One-time database setup script
└── data/
    └── blindspot.db                         # created using Kaggle .csv dataset
    └── resume_screening.csv                 # Kaggle dataset (not committed)
```

---

## Prerequisites

- Python 3.10 or higher
- An Anthropic API key (get one at https://console.anthropic.com)
- The Kaggle resume screening dataset CSV

---

## Setup Instructions

### Step 1 — Clone the repository

```bash
git clone https://github.com/iiadarsh-cognizant/blind-resume-screening.git
cd blind-resume-screening
```

### Step 2 — Create and activate a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install neuro-san-studio
pip install flask flask-cors requests
```

### Step 4 — Set your Anthropic API key

**Windows (permanent — recommended):**

Press `Win + R`, type `rundll32 sysdm.cpl,EditEnvironmentVariables`, add a User Variable:
- Name: `ANTHROPIC_API_KEY`
- Value: `sk-ant-your-key-here`

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Step 5 — Download the dataset / or use existing dataset provided in data folder

Download from: https://www.kaggle.com/datasets/mdtalhask/ai-powered-resume-screening-dataset-2025

Place the CSV file at:
```
data/resume_screening.csv
```

### Step 6 — Set up the database / Not needed if using existing blindspot.db from data folder

```bash
python setup_database.py
```

Expected output:
```
Database created successfully
Available job roles:
  AI Researcher: 514 candidates
  Cybersecurity Analyst: 510 candidates
  Data Scientist: 510 candidates
  Software Engineer: 466 candidates
```

---

## Running the Application

You need **two terminals** running simultaneously.

### Terminal 1 — Start Neuro SAN

```bash
cd blind-resume-screening
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
ns run
```

Wait until you see:
```
Neuro-San server is now running.
nsflow client started on localhost:4173
```

### Terminal 2 — Start Flask

```bash
cd blind-resume-screening/webapp
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
python app.py
```

### Step 3 — Open the UI

Navigate to:
```
http://localhost:5000
```

The green **"Neuro SAN connected"** badge in the top bar confirms both services are communicating.

---

## Demo Walkthrough

1. **Open roles** — Select a job role (e.g., Data Scientist)
2. **Applicant pool** — View all real applicants with full identity visible
3. **Blind screening** — Click "Run ranking agent". Claude evaluates candidates with zero PII. Watch the live timer and trace panel during the execution.
4. **Approve & reveal** — Drag the slider to choose top-N. Click "Approve & reveal" to release only those identities.
5. **Schedule interviews** — Confirm interview slots one by one or all at once.
6. **Agent network** — View the architecture diagram and real run statistics.

---

## Configuration

To change the LLM model, edit `config/llm_config.hocon`:

```hocon
{
    "llm_config": {
        "model_name": "claude-sonnet-4-5"
    }
}
```

---

## Files included in this repo 
- `data/blindspot.db` — generated locally by `setup_database.py`
- `data/resume_screening.csv` — download from Kaggle

## Files NOT included in this repo

These are excluded via `.gitignore` for security and size reasons:
- `.env` — contains your API key
- `venv/` — created locally
- `__pycache__/` — generated at runtime


## Limitations & Future Work

Blindspot is a working prototype built to demonstrate a privacy-first agent architecture, not a production ATS. Known limitations:
- **Single-pass ranking** — `RankingAgent` scores the full candidate pool once, with no iterative self-critique or multi-pass consensus scoring. The token-accounting audit trail provides observability, but not an evaluation loop in the strict sense.
- **Free-text response parsing** — the ranked list is extracted from the orchestrator's final message via a structured `<<<RANKING>>>` JSON block, with a markdown-regex parser and a raw score-sort as fallbacks. This is robust in practice but not schema-guaranteed, since the underlying response is still LLM-generated text.
- **Run time and cost** — a full screening run takes ~2-3 minutes and consumes a non-trivial number of tokens per job role, since all candidates are evaluated in a single pipeline pass. This doesn't obviously scale to thousands of candidates without batching or a cheaper pre-filter stage.
- **Static, hardcoded scheduling data** — `AvailabilityMatcherTool` matches against fixed sample calendars rather than a live calendar integration.
- **Single job role per run** — the pipeline screens one role at a time; there's no cross-role batch mode or comparative dashboard.
- **Demo dataset** — built on a static Kaggle CSV, not connected to a real applicant tracking system.

Planned improvements:

- Integrate real calendar APIs (Google Calendar / Outlook) in place of hardcoded availability windows
- Add an iterative evaluation loop — e.g., a second-pass "critique" agent that reviews `RankingAgent`'s justifications before finalizing scores
- Persist run history and token accounting to the database for a durable audit trail, instead of console-only logging
- Support multi-role batch screening in a single run
- Replace text-based ranking extraction with a fully schema-enforced structured output once broader tool/function-calling support stabilizes in Neuro SAN
