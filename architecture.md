# Architecture — Blindspot Blind Hiring Pipeline

## Overview

Blindspot is a privacy-first multi-agent hiring pipeline built on the Neuro SAN framework. It solves a real problem in AI-assisted recruiting: when an LLM evaluates candidate resumes, it can be inadvertently influenced by names, genders, or other identity signals embedded in the text. Blindspot eliminates this risk entirely by using Neuro SAN's `sly_data` mechanism as a structural privacy firewall — candidate identities are cryptographically separated from the evaluation pipeline before any LLM reasoning occurs.

---

## The Core Problem

Traditional AI resume screening passes full candidate profiles, including names and personal details, to an LLM for evaluation. Even with instructions to "ignore names," research shows LLMs exhibit measurable bias based on name-derived signals. Blindspot makes bias structurally impossible rather than relying on prompt-level instructions.

---

## Neuro SAN Agent Network

The entire pipeline is defined in a single HOCON configuration file (`registries/blindspot.hocon`) and runs on the Neuro SAN framework using the AAOSA (Adaptive Agent-Oriented Software Architecture) protocol.

### Agent Network Diagram

```
User Request
     │
     ▼
┌─────────────────────────────┐
│   RecruitingOrchestrator    │  ← Frontman LLM Agent
│   (claude-sonnet-4-5)       │    Receives: job_role, top_n
│   Coordinates full pipeline │    Orchestrates sequence
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   ResumeAnonymizerTool      │  ← CodedTool (Python)
│   coded_tools/blindspot/    │    Queries SQLite database
│   resume_anonymizer.py      │    ════════════════════
│                             │    sly_data["Candidate_01"] = {
│                             │      name: "John Smith",      ← SEALED
│                             │      resume_id: "R001"        ← SEALED
│                             │    }
│                             │    Returns to chat stream:
│                             │    { candidate_id, skills,
│                             │      experience, education }  ← ONLY THIS
└──────────────┬──────────────┘
               │  (anonymized profiles only — NO names)
               ▼
┌─────────────────────────────┐
│   RankingAgent              │  ← LLM Agent (Claude)
│   (claude-sonnet-4-5)       │    Sees: Candidate_01, skills,
│                             │    experience, education ONLY
│                             │    Produces: ranked list with
│                             │    scores + justifications
│                             │    ⚠ NEVER receives real names
└──────────────┬──────────────┘
               │  (ranked candidate IDs + scores)
               ▼
┌─────────────────────────────┐
│   IdentityResolverTool      │  ← CodedTool (Python)
│   identity_resolver.py      │    Reads sly_data
│                             │    Releases ONLY top-N names
│                             │    All others: permanently sealed
│                             │    allow: top N only
└──────────────┬──────────────┘
               │  (approved candidates with real names)
               ▼
┌─────────────────────────────┐
│   SchedulingAgent           │  ← LLM Agent (Claude)
│   (claude-sonnet-4-5)       │    Coordinates interview slots
│                             │    Calls AvailabilityMatcherTool
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   AvailabilityMatcherTool   │  ← CodedTool (Python)
│   availability_matcher.py   │    Pure calendar math
│                             │    No LLM involvement
│                             │    Deterministic slot matching
└─────────────────────────────┘
```

---

## The sly_data Privacy Firewall

`sly_data` is a protected side-channel in Neuro SAN that is:
- **Never serialised into any LLM prompt** — structurally impossible, not just instructed
- **Accessible only to CodedTools** — Python code, not LLM agents
- **Shared across the agent network** as a bulletin board for tool cooperation

In Blindspot, the `ResumeAnonymizerTool` writes to `sly_data`:

```python
sly_data[candidate_id] = {
    "name": row["name"],
    "resume_id": row["resume_id"]
}
```

And the `IdentityResolverTool` reads from `sly_data`, but only releases identities for the top-N approved candidates:

```python
approved = ranked_ids[:top_n]      # Only top N
resolved = [sly_data[cid] for cid in approved]
# Everyone else: permanently sealed, never accessible
```

The `RankingAgent` (Claude) sits between these two tools and only ever sees:

```
Candidate_01 | Python, TensorFlow, Spark | 7 years | Masters | AWS cert | 8 projects
Candidate_02 | R, SQL, scikit-learn | 4 years | Bachelors | None | 3 projects
...
```

No names. No emails. No personal identifiers. Bias is structurally eliminated.

---

## Data Flow

```
Kaggle CSV
    │
    ▼ (setup_database.py)
SQLite Database (blindspot.db)
    │  Table: applicants
    │  Columns: resume_id, name, skills, experience_years,
    │           education, certifications, job_role, ai_score
    │
    ▼ (ResumeAnonymizerTool)
Two streams split here:
    │
    ├──► sly_data channel ──────────────────────► IdentityResolverTool only
    │    { Candidate_01: {name, resume_id} }        (never seen by LLMs)
    │
    └──► Chat stream ──────────────────────────► RankingAgent (Claude)
         { candidate_id, skills, experience,         (anonymized only)
           education, certifications, projects }
```

---

## System Architecture

```
Browser (localhost:5000)
        │
        │ HTTP/XHR
        ▼
Flask Web Server (app.py, port 5000)
        │
        │ HTTP POST /api/v1/blindspot/streaming_chat
        ▼
Neuro SAN Engine (port 8080)
        │
        ├── Agent: RecruitingOrchestrator
        │       └── Claude claude-sonnet-4-5
        ├── Agent: RankingAgent
        │       └── Claude claude-sonnet-4-5
        ├── Agent: SchedulingAgent
        │       └── Claude claude-sonnet-4-5
        ├── CodedTool: ResumeAnonymizerTool
        │       └── SQLite query → sly_data write
        ├── CodedTool: IdentityResolverTool
        │       └── sly_data read → selective reveal
        └── CodedTool: AvailabilityMatcherTool
                └── Deterministic slot matching
```

---

## Coded Tools (Python)

### ResumeAnonymizerTool
- Queries `applicants` table filtered by `job_role`
- Assigns sequential `Candidate_XX` IDs
- Seals `name` and `resume_id` into `sly_data`
- Returns only anonymized fields to the chat stream

### IdentityResolverTool
- Receives ranked `candidate_ids` and `top_n` parameter
- Reads real identities from `sly_data` for top-N only
- Returns approved candidates with names revealed
- Candidates outside top-N are never accessed — permanently sealed

### AvailabilityMatcherTool
- Takes a candidate name and finds the first overlapping slot between hardcoded candidate and interviewer availability windows
- Pure Python — no LLM involvement
- Guarantees deterministic, reproducible scheduling

---

## HOCON Configuration

The entire agent network is declared in `registries/blindspot.hocon`. Key design decisions:

- `model_name: "claude-sonnet-4-5"` used for all LLM agents
- Coded tools reference Python classes via the `class` field
- Tool parameters are typed using JSON Schema — Neuro SAN validates at startup
- The frontman (`RecruitingOrchestrator`) is the first tool in the `tools` array
- The recruiter chooses how many candidates to approve **before** the run starts (a `top_n` field in the UI, default 3). `RecruitingOrchestrator` passes this straight through to `IdentityResolverTool`, so it's the same number that gets formally resolved and the same number the reveal slider is capped to afterward — there's no separate post-hoc "reveal more" path beyond what was actually resolved.
- When the Flask web UI calls the pipeline, its request explicitly asks the orchestrator to also emit a `<<<RANKING>>>...<<<END>>>` block containing a strict JSON array (`candidate_id`, `name`, `score`, `justification`) for the approved candidates, in addition to its normal narrated summary. This gives the frontend a reliable, machine-parseable result instead of relying on scraping prose. Requests that don't ask for that block (e.g. a person chatting directly through Neuro SAN's own web client) simply get the normal narrated summary, unchanged.

---

## Ranking Basis

Candidate ranking is produced **live by `RankingAgent`** at request time, based purely on the anonymized skills/experience/education/certifications/project-count fields it receives — it is not a lookup against a pre-computed dataset column. The CSV's original `AI Score (0-100)` field is retained in the database purely as descriptive source data (and as a same-source ordering fallback for the small remainder of candidates the agent doesn't individually name), not as the mechanism that decides the ranking recruiters see.

---

## Privacy Guarantee

At no point during the pipeline does any LLM agent receive:
- Candidate real names
- Email addresses
- Resume IDs
- Any other personally identifiable information

This guarantee is **structural** — enforced by the Neuro SAN `sly_data` architecture — not prompt-level. Even if the LLM were instructed to reveal names, it would have no names to reveal.

The `IdentityResolverTool` logs every release, e.g.:
```
[BLINDSPOT] 3 identities released. 47 candidates permanently sealed.
```
(exact counts depend on the job role's applicant pool size and the top-N value chosen for that run)

---

## Dataset

**AI-Powered Resume Screening Dataset (2025)** from Kaggle
Source: https://www.kaggle.com/datasets/mdtalhask/ai-powered-resume-screening-dataset-2025

| Field | Description |
|---|---|
| Resume_ID | Unique candidate identifier |
| Name | Candidate full name (sealed into sly_data) |
| Skills | Technical skills list |
| Experience (Years) | Years of experience |
| Education | Highest education level |
| Certifications | Professional certifications |
| Job Role | Target role (used for filtering) |
| AI Score (0-100) | Original dataset score, kept as reference/fallback data — not the live ranking mechanism (see "Ranking Basis" above) |

Current local database (`data/blindspot.db`):

| Job Role | Candidates |
|---|---|
| AI Researcher | 514 |
| Cybersecurity Analyst | 510 |
| Data Scientist | 510 |
| Software Engineer | 50 *(trimmed down for cost-efficient local testing — see README)* |

**Total: 1,584 candidates.** Counts will differ if you regenerate the database from the full Kaggle CSV via `setup_database.py` without trimming.
