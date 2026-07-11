# Blindspot — Project Summary

## The Problem

AI-assisted resume screening is increasingly common in enterprise hiring, but it carries a hidden risk: even well-instructed LLMs can exhibit measurable bias when processing candidate profiles that contain names, email addresses, and other identity signals. Research has shown models score identical resumes differently when only the candidate's name changes. This is not a failure of the prompt — it is a structural limitation of passing PII into any language model's context.

Traditional solutions ask the LLM to "ignore" personal information. Blindspot takes a different approach: it makes bias **structurally impossible** rather than merely instructed away.

---

## The Solution

Blindspot is a multi-agent blind hiring pipeline built on Cognizant's Neuro SAN framework. It automates the full screening lifecycle — anonymous candidate ranking, recruiter-approved identity reveal, and interview scheduling — using Neuro SAN's `sly_data` mechanism as a structural privacy firewall that prevents any LLM from ever seeing a candidate's real identity during evaluation.

The system runs against a real Kaggle dataset (currently 1,584 candidates across 4 job roles in the local database) and provides a full web UI for recruiters to run and observe the pipeline end to end.

---

## How It Works

The pipeline is six agents/tools defined in a single HOCON configuration file, orchestrated by Neuro SAN:

1. **RecruitingOrchestrator** — Claude frontman agent; receives the recruiter's job role and top-N choice, coordinates the pipeline sequentially.
2. **ResumeAnonymizerTool** — Python CodedTool. Queries SQLite for candidates matching the job role, seals each candidate's real name and resume ID into `sly_data` (never serialized into any LLM prompt), and returns only anonymized fields (skills, experience, education, certifications, project count) to the chat stream.
3. **RankingAgent** — Claude LLM agent. Sees only anonymized profiles — no names, no PII — and produces a live, merit-based ranked list with scores and one-sentence justifications.
4. **IdentityResolverTool** — Python CodedTool. Reads `sly_data` and releases real identities for only the top-N candidates the recruiter approved before the run started. Everyone else stays permanently sealed and is never accessed.
5. **SchedulingAgent** — Claude LLM agent. Coordinates interview scheduling for approved candidates via AvailabilityMatcherTool.
6. **AvailabilityMatcherTool** — Deterministic Python CodedTool. Finds the first overlapping slot between candidate and interviewer calendars. No LLM involved in the actual scheduling math.

The recruiter chooses how many candidates to approve **before** clicking "run," so the number that's actually resolved by `IdentityResolverTool` and the number the UI later lets you reveal are always the same value — there's no separate mechanism that can reveal more than what was genuinely processed.

---

## The Privacy Innovation

The core technical innovation is using Neuro SAN's `sly_data` channel as a structural privacy boundary, rather than a prompt-engineering instruction. `sly_data` is:

- **Never included in any LLM context window** — by architecture, not by instruction
- **Only accessible to Python CodedTools** — LLM agents have no mechanism to read it
- **Shared as a bulletin board** between tools across the agent network

This makes the privacy guarantee architectural: `RankingAgent` is incapable of seeing candidate names regardless of how it's prompted. Bias elimination is a property of the system design, not the model's compliance.

The final ranked list shown to the recruiter is built from `RankingAgent`'s live output for that run (matched back to full candidate records after the fact) — not a pre-computed dataset column. The original Kaggle "AI Score" field is kept only as reference data and as a fallback ordering for the majority of candidates who remain sealed and were never individually named.

---

## Web User Interface

Blindspot includes a full-featured dark-themed dashboard built with Flask and vanilla HTML/CSS/JavaScript. The UI walks recruiters through the complete pipeline in six steps:

1. **Open roles** — Job roles and candidate counts loaded directly from the SQLite database
2. **Applicant pool** — Full candidate list with identity visible (pre-screening state)
3. **Blind screening** — Split-panel view showing the anonymized chat stream on the left and sealed identity placeholders on the right. A live elapsed timer, rotating status messages, and a progress bar keep users informed during the agent run.
4. **Approve & reveal** — Recruiter sets top-N using an interactive slider. Only the approved identities are revealed; all others remain blurred.
5. **Schedule interviews** — Individual or bulk confirmation with toast notifications confirming calendar invites.
6. **Agent network** — Architecture diagram with live run statistics: candidates screened, identities sealed, LLM token usage, API cost, time saved.

---

## Technical Stack

| Component | Technology |
|---|---|
| Multi-agent framework | Neuro SAN (neuro-san-studio) |
| LLM | Anthropic Claude claude-sonnet-4-5 |
| Agent configuration | HOCON declarative format |
| Coded tools | Python 3.10+ (CodedTool interface) |
| Database | SQLite |
| Web backend | Flask |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Dataset | AI-Powered Resume Screening Dataset 2025 (Kaggle) |

---

## Key Technical Decisions

**Why Neuro SAN over LangChain/CrewAI?** `sly_data` has no direct equivalent in other frameworks — it's a first-class primitive for passing private data between agents without it ever entering an LLM's context. This was the essential requirement for Blindspot's privacy guarantee.

**Why SQLite?** The dataset is static for this demonstration. SQLite gives real query semantics (filter by job role, order by score) with zero infrastructure dependencies, keeping the project self-contained and easy to reproduce.

**Why deterministic scheduling?** Interview slot-matching has a definitive correct answer; using an LLM for calendar math would add cost, latency, and non-determinism for no benefit. `AvailabilityMatcherTool` is exact and reproducible.

**Why declarative HOCON?** The six-agent network is defined without Python code for the agent logic itself, demonstrating Neuro SAN's core proposition — sophisticated multi-agent systems built declaratively.

---

## Results and Impact

When run against the Data Scientist job role (510 candidates):

- **510 candidates evaluated** in a single pipeline run
- **Zero PII** exposed to any LLM during evaluation
- **Top-N candidates** revealed only after recruiter approval
- **Remaining candidates** permanently sealed — identities never accessed
- Estimated **1,785 minutes** of manual screening time saved per run
- Full audit trail via Neuro SAN's token accounting

---

## Limitations & Evaluation

Blindspot currently performs a **single ranking pass** per run — `RankingAgent` scores the pool once, with the token-accounting log serving as the audit trail rather than an iterative self-critique loop. See `README.md` for the full list of known limitations and planned improvements (live calendar integration, multi-pass evaluation, multi-role batch screening).

---

## Conclusion

Blindspot demonstrates that a multi-agent framework's structural properties can provide stronger privacy guarantees than prompt engineering alone. By using Neuro SAN's `sly_data` channel as an architectural boundary, the system makes identity-based bias structurally impossible — not just discouraged — regardless of model version or prompt phrasing. It's a practical pattern for any AI system that must reason over sensitive data: separate the data from the reasoning using the framework's architecture, not the model's instructions.

