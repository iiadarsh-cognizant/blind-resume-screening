# Blindspot — Project Summary

## The Problem

AI-assisted resume screening is increasingly common in enterprise hiring, but it carries a hidden risk: even well-instructed LLMs can exhibit measurable bias when processing candidate profiles that contain names, email addresses, and other identity signals. Research has demonstrated that models assign different scores to identical resumes when only the candidate's name changes. This is not a failure of the prompt — it is a structural limitation of passing PII into any language model context.

Traditional solutions ask the LLM to "ignore" personal information. Blindspot takes a fundamentally different approach: it makes bias **structurally impossible** rather than merely instructed away.

---

## The Solution

Blindspot is a multi-agent blind hiring pipeline built on Cognizant's Neuro SAN framework. It automates the full screening lifecycle — from anonymous candidate ranking to identity reveal to interview scheduling — while using Neuro SAN's `sly_data` mechanism as a cryptographic-style privacy firewall that prevents any LLM from ever seeing a candidate's real identity during evaluation.

The system processes a real dataset of 2,000 candidates across 4 job roles and provides a full-featured web UI for recruiters to interact with the pipeline.

---

## How It Works

The pipeline consists of six agents defined in a single HOCON configuration file and orchestrated by the Neuro SAN framework:

**1. RecruitingOrchestrator** — A Claude-powered frontman agent that receives the recruiter's request (job role + top-N count) and coordinates the full pipeline sequentially.

**2. ResumeAnonymizerTool** — A Python CodedTool that queries a SQLite database for all candidates matching the requested job role. It seals each candidate's real name and resume ID into Neuro SAN's `sly_data` channel — a protected side-channel that is never serialised into any LLM prompt. It returns only anonymized fields (skills, experience, education, certifications, project count) to the chat stream.

**3. RankingAgent** — A Claude LLM agent that receives only the anonymized candidate profiles. It has no access to names, emails, or any PII. It evaluates each candidate purely on merit and produces a ranked list with scores (0-100) and one-sentence justifications for each candidate.

**4. IdentityResolverTool** — A Python CodedTool that reads from `sly_data` and releases real identities for only the top-N approved candidates. All other candidates remain permanently sealed — their identities are never accessed or returned.

**5. SchedulingAgent** — A Claude LLM agent that coordinates interview scheduling for approved candidates by calling the AvailabilityMatcherTool for each one.

**6. AvailabilityMatcherTool** — A deterministic Python CodedTool that finds the first overlapping availability slot between a candidate and an interviewer using hardcoded calendar data. No LLM is involved in scheduling logic.

---

## The Privacy Innovation

The key technical innovation is the use of Neuro SAN's `sly_data` channel as a structural privacy boundary. Unlike prompt-engineering approaches that instruct models to ignore certain fields, `sly_data` is:

- **Never included in any LLM context window** — by the architecture, not by instruction
- **Only accessible to Python CodedTools** — LLM agents have no mechanism to read it
- **Shared as a bulletin board** between tools across the agent network

This means the privacy guarantee is cryptographic in nature: the RankingAgent (Claude) is architecturally incapable of seeing candidate names, regardless of how it is prompted. The bias elimination is a property of the system design, not of the model's compliance.

---

## Web User Interface

Blindspot includes a full-featured dark-themed dashboard built with Flask and vanilla HTML/CSS/JavaScript. The UI walks recruiters through the complete pipeline in six steps:

1. **Open roles** — Job roles and candidate counts loaded directly from the SQLite database
2. **Applicant pool** — Full candidate list with identity visible (pre-screening state)
3. **Blind screening** — Split-panel view showing the anonymized chat stream on the left and sealed identity placeholders on the right. A live elapsed timer, rotating status messages, and a progress bar keep users informed during the ~5 minute agent run.
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

**Why Neuro SAN over LangChain/CrewAI?**  
Neuro SAN's `sly_data` mechanism has no direct equivalent in other frameworks. It provides a first-class architectural primitive for passing private data between agents without it entering any LLM context. This was the essential requirement for Blindspot's privacy guarantee.

**Why SQLite?**  
The dataset is static for this demonstration. SQLite provides real database query semantics (filtering by job role, ordering by score) without infrastructure dependencies, making the project fully self-contained and easy to reproduce.

**Why deterministic scheduling?**  
Interview scheduling is a matching problem with a definitive correct answer. Using an LLM for calendar math introduces unnecessary cost, latency, and non-determinism. The `AvailabilityMatcherTool` guarantees reproducible results in milliseconds.

**Why declarative HOCON configuration?**  
The entire six-agent network is defined in a single `blindspot.hocon` file without Python code for the agent logic. This demonstrates Neuro SAN's core proposition: domain experts can build sophisticated multi-agent systems without programming skills.

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

## Conclusion

Blindspot demonstrates that the structural properties of a multi-agent framework can provide stronger privacy guarantees than any prompt-engineering approach. By using Neuro SAN's `sly_data` channel as an architectural privacy boundary, the system guarantees bias-free candidate evaluation at the framework level — making it impossible for any LLM to exhibit identity-based bias, regardless of model version or prompt variation.

The project shows a practical, production-ready pattern for any AI system that must handle sensitive data: separate the data from the reasoning using the framework's architecture, not the model's instructions.
