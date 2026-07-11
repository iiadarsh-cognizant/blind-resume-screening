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

### Step 5 — Download the dataset

Download from: https://www.kaggle.com/datasets/mdtalhask/ai-powered-resume-screening-dataset-2025

Place the CSV file at:
```
data/resume_screening.csv
```

### Step 6 — Set up the database

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
3. **Blind screening** — Click "Run ranking agent". Claude evaluates candidates with zero PII. Watch the live timer and trace panel during the ~5 minute run.
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

## Files NOT included in this repo

These are excluded via `.gitignore` for security and size reasons:
- `data/blindspot.db` — generated locally by `setup_database.py`
- `data/resume_screening.csv` — download from Kaggle
- `.env` — contains your API key
- `venv/` — created locally
- `__pycache__/` — generated at runtime
