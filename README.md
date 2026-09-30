# SetuCare

**Interoperability middleware for government services.**
A thin layer that lets independent government systems talk to each other — without replacing any of them.

---

## The problem

Government departments run separate portals, apps and databases, built independently, on different data formats, identifiers, and APIs. The result: citizens re-submit the same information at every office, officials have no consolidated view of a citizen's applications and approvals, and nobody can track one request across three departments.

**SetuCare doesn't replace these systems. It sits between them.**

---

## What it does

A citizen applies once. SetuCare pulls their existing records from every department that already has them, verifies eligibility automatically where it can, tracks the whole thing as one application with one timeline, and gives officials a single dashboard across all of it — with consent, audit and access control built in, not bolted on.

---

## Architecture

```
 ┌─────────────────────────────────────────────┐
 │   Citizen page          Official dashboard   │   ← plain HTML/CSS/JS
 └─────────────────────────────────────────────┘
                        │
 ┌─────────────────────────────────────────────┐
 │              SetuCare middleware              │
 │                                               │
 │  Consent manager   →  Workflow engine (JSON)   │
 │  Golden record      →  Unified tracker         │
 │  Event bus           →  Audit log (hash-chain) │
 └─────────────────────────────────────────────┘
                        │
 ┌─────────────────────────────────────────────┐
 │        Connectors (one per department)        │
 └─────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
   Pension API     Municipal CSV     Ration XML
   (modern REST)   (legacy file)     (legacy service)
```

One FastAPI codebase, one SQLite database file. No Docker, no message broker, no frontend framework — deliberately, so the interoperability pattern stays visible instead of hidden behind infrastructure.

---

## Core capabilities

### 1. Talking to the different systems — the interoperability layer
- **Connectors**, one per department, each translating its native format (REST/JSON, legacy CSV, legacy XML) into one shared model.
- **Canonical data model** — a single agreed shape for a `Person` and an `Application`. Every connector translates to and from it, so adding a system means writing one translator, not one per existing system.
- **API gateway** (`gateway.py`) — every cross-department fetch goes through one enforcement point, which checks consent before any data moves.

### 2. Knowing who is who, and who allowed what
- **Master-data management (golden record)** — one trusted profile per citizen, built by merging what each department separately knows.
- **Entity resolution** — deciding that `"R. Kumar"` (Municipal) and `"Ramesh Kumar"` (Pension) are the same person, using normalized name + date-of-birth matching with a confidence score. Exact matches, fuzzy matches (e.g. an abbreviated name), and non-matches are all handled explicitly, not merged blindly.
- **Consent management** — a citizen grants consent once, for a named purpose, for named fields, until an expiry date, and can revoke it. Every grant, use and revocation is logged. No connector will return department data without an active consent record covering it.
- **Federated identity / mock SSO** — one login is recognised across the whole system. (This demo uses a mock login; a real deployment would use OpenID Connect against a government identity provider.)

### 3. Making things move
- **Workflow orchestration** — approval steps are defined in a JSON file, not in code. Reordering steps, changing an SLA, or adding a new department to a workflow means editing configuration.
- **Event-driven notifications** — when a step completes, an event is published; subscribers react independently (advancing the workflow, writing a mock SMS/email). Adding a new reaction never touches the workflow engine itself.
- **Unified application tracking** — one application ID, one status timeline, however many departments are involved behind the scenes.

### 4. Trust and safety
- **Role-based access control** — citizen, clerk, officer and admin roles each see and can do only what their role permits, enforced on every API call, not just hidden in the UI.
- **Tamper-evident audit log** — every action is recorded as a hash-chained row, each one storing the fingerprint of the row before it. Editing or deleting any past row breaks the chain in a way that's detectable and locatable.
- **Data-quality checks** — records are checked at the door (a valid phone number, a plausible date of birth); failures are flagged rather than silently passed through.
- **Exception handling** — failed connector calls are retried before being set aside in a dead-letter list; SLA breaches surface automatically in an exception queue instead of getting lost in logs.

### 5. Seeing what is happening
- **Monitoring dashboard** — applications by status, SLA compliance %, average processing time, connector health, open exceptions, fields citizens didn't have to retype, and duplicate profiles avoided through entity resolution.

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI |
| Database | SQLite (single file — "Reset demo" simply recreates it) |
| Frontend | Plain HTML / CSS / JS, no framework |
| Departments (mocked) | Pension (REST/JSON), Municipal (legacy CSV), Ration (legacy XML) |

A production deployment would move to a managed database (e.g. MySQL/Postgres) and real per-department authentication; both are called out explicitly as future scope below, not silently assumed.

---

## Project structure

```
setucare/
├── main.py                    FastAPI app, mock department endpoints, static file mount
├── models.py                  Canonical Person / Application models
├── normalize.py                Name/date normalization helpers
├── connectors.py               One connector per department
├── matching.py                 Identity-matching / confidence scoring
├── golden.py                   Golden record creation + merge
├── consent.py                  Consent grant / revoke / enforcement
├── gateway.py                  Single enforcement point for cross-department fetches
├── applications.py              Application creation + prefill
├── workflow.py                  JSON-driven workflow engine + SLA tracking
├── events.py                    Event bus + mock notifications
├── subscribers.py               Event reactions (decoupled from the workflow engine)
├── issues.py                    Exception queue + dead-letter list
├── quality.py                   Data-quality rules
├── stats.py                     Dashboard aggregate statistics
├── users.py                     Mock user directory (RBAC roles)
├── rbac.py                      Role resolution + enforcement
├── audit.py                     Hash-chained audit log
├── api.py                       All API routes
├── db.py                        SQLite schema + connection handling
├── workflows/
│   ├── pension.json             Pension approval workflow
│   └── ration_renewal.json      Ration card renewal workflow
├── data/
│   └── municipal_residents.csv  Mock legacy municipal data
└── static/
    ├── login.html                Mock SSO
    ├── citizen.html               Citizen application + tracker view
    ├── dashboard.html              Official dashboard
    ├── exceptions.html             Exception queue + dead-letter view
    ├── audit.html                  Audit log + chain verification
    ├── matches.html                Identity-matching visualizer
    ├── about.html                  About / scope / data notice
    ├── 404.html                    Custom not-found page
    └── nav.js                      Shared navigation
```

---

## Running it locally

```bash
git clone <your-repo-url>
cd setucare

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/` and pick a user from the dropdown.

### Try it as a citizen
Log in as **Ramesh Kumar** → **Apply for Pension**. Watch the tracker fill in as the age and income checks run automatically, using data pulled — with consent — from the Municipal and Ration systems, without Ramesh retyping a single field twice.

Log in as **Sita Devi** and apply — her income exceeds the eligibility threshold, and the system rejects that step automatically, with the reason visible on her tracker.

### Try it as staff
Log in as **Anil — Pension Officer** to approve Ramesh's application from the dashboard. Log in as **Admin** or **Priya — Clerk** to browse the dashboard, exception queue, audit log, and identity-matching view.

---

## Demo story (3 minutes)

1. Citizen logs in (mock SSO) and applies once, granting consent once.
2. Connectors pull records from all three departments into one canonical format — the form is pre-filled.
3. A JSON-defined workflow runs the eligibility checks across departments; the tracker shows one timeline.
4. An SLA breach or a rejected application surfaces in the exception queue and on the dashboard.
5. Close on the "fields not retyped" counter and the tamper-evident audit log.

---

## What's mocked, and why

This is a working prototype built to demonstrate the pattern, not a production system. The following are intentionally simulated:

| Mocked | Real equivalent |
|---|---|
| Dropdown login | OpenID Connect / real federated SSO |
| Three sample department systems | Real department APIs, databases and legacy systems |
| SMS/email as database rows | Real SMS/email gateways |
| A fixed ID crosswalk between departments | Real person-lookup by name/DOB per department, or a shared identifier registry |
| SQLite | A production database (e.g. MySQL/Postgres) |

No real Aadhaar, DigiLocker, or API Setu integration is used or claimed.

---

## Future scope

- Real OIDC-based federated identity
- Integration with API Setu / DigiLocker for genuine cross-government data exchange
- A full data-quality rule engine (beyond the two illustrative rules here)
- Real SMS/email delivery
- Multi-tenant scale and production security hardening (secrets management, rate limiting, encryption at rest)
- Automated background SLA monitoring (currently checked on demand)
- A visual workflow designer, and conditional/parallel workflow steps

---

## Data & privacy

All citizens, applications and records in this prototype are fictional, created for demonstration purposes only. No real personal data is collected, stored, or transmitted. See `static/about.html` for the in-app notice.

---

## License

Built for a hackathon submission. Add a license here if you intend to reuse or open-source this beyond the event.
