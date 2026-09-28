You are my hackathon build mentor and pair programmer. I am building a working, demoable prototype SOLO in about 2 days. Help me build it one small, testable step at a time.

## PROJECT: JanSetu (interoperability middleware for government services)

PROBLEM STATEMENT
Government departments run multiple portals, apps, registries and databases built independently. Data formats, identifiers, authentication, APIs and process definitions differ, so citizens re-submit the same information, track applications across portals, and visit multiple offices. Officials lack a consolidated view of beneficiaries, applications, approvals, grievances and outcomes. The challenge is secure, standards-based interoperability WITHOUT replacing existing systems.

EXPECTED SOLUTION
A middleware / federated service-delivery layer with: API-based exchange, common data standards, master-data management, consent-based data sharing, SSO/federated identity, event-driven notifications, unified application tracking, configurable workflow orchestration, reusable connectors for legacy and modern systems, audit logs, RBAC, data-quality checks, exception handling and monitoring dashboards. Outcomes: fewer duplicate submissions, faster processing, consistent records, better citizen experience, cross-department coordination, measurable SLA compliance.

## MY SOLUTION SHAPE
A thin middleware layer between existing systems. It does not replace them.
- Top: citizen page + official dashboard (plain HTML/JS, no framework).
- Middle (one FastAPI codebase, one database): consent manager, workflow engine, event bus (a table + function call, no Kafka), master/golden record, unified tracker, audit log.
- Bottom: connector layer, one connector per department, each translating to a common canonical model.
- Three deliberately messy mock departments:
  1. Pension: modern REST/JSON. Fields: beneficiary_id, full_name, dob (YYYY-MM-DD), phone, bank_account, pension_status. Where the citizen applies.
  2. Municipal: legacy CSV file (data/municipal_residents.csv). Fields: RES_NO, NAME (uppercase, "R. KUMAR"), BIRTH_DT (DD/MM/YYYY), ADDR, WARD. Confirms age and residence.
  3. Ration card: old XML service. Fields: rationCardNo, headOfFamily, dateOfBirth (DD-Mon-YYYY), annualIncome, familyMembers. Confirms household and income.
Test person: Ramesh Kumar, born 14 March 1958, appears as PEN-1001, MUN-77, BR-0099. Second person: Sita Devi (PEN-1002, MUN-78, BR-0100), whose income of 310000 fails the income rule.

## TECH STACK (fixed, do not suggest alternatives)
Python + FastAPI + SQLite (one file, so "Reset demo" = recreate the DB), plain HTML/CSS/JS pages served by FastAPI. Production choice (MySQL) is mentioned on a slide only. No Docker, no message brokers, no frontend framework.

## CORE FEATURES TO BUILD (real)
1. Connectors + canonical data model: one common "Person" and "Application" format. Each connector has fetch(external_id) -> canonical dict. Normalize names, dates to ISO, IDs into a common structure.
2. Master record (golden record) + identity matching: link PEN/MUN/BR records into one citizen. Primary match on normalized name + DOB; USP: show one fuzzy match ("R. KUMAR" vs "Ramesh Kumar") with a confidence score. Store source-system links per citizen.
3. Consent management: citizen grants consent once (purpose, fields, expiry); connectors REFUSE to fetch without active consent; consent can be revoked. Every grant/use/revoke is logged.
4. Application creation: citizen applies once for a pension; pre-filled from pulled data. Track a "fields not retyped" counter (number of fields auto-filled instead of typed).
5. Configurable workflow engine: workflow defined in a JSON file, not code. Steps like: verify_age (Municipal), verify_income (Ration), approve (Pension officer), each with department, rule, and sla_hours. Adding or reordering a step = edit JSON only.
6. Unified tracker: one application ID, one status timeline across all departments (submitted -> age verified -> income verified -> approved/rejected).
7. Audit log: append-only table of who did what, when; USP: hash-chained rows (each row stores hash of the previous row) to show tamper evidence.
8. Events + notifications: an events table; publishing an event triggers subscribers (advance the workflow, write a mock SMS/email to a notifications table shown in the UI).
9. SLA breach + exception queue: one seeded application is overdue; it appears in the exception queue and on the dashboard. Failed connector calls get retried, then land in a dead-letter list.
10. Data-quality checks: exactly two rules (phone must be 10 digits; DOB must be a valid date and age plausible). Failures go to the exception queue.
11. Official dashboard: counts by status, SLA compliance %, average processing time, exception queue, connector health, "fields not retyped" total, duplicates avoided.
12. RBAC with mock login: roles citizen, clerk, officer, admin; pick a user from a dropdown (mock SSO, I explain OIDC in the pitch). Officers see the dashboard and can approve; citizens see only their own applications.
13. "Reset demo" button that re-seeds all data so the demo is repeatable.

## MOCK OR FUTURE SCOPE (do NOT build; warn me if I drift)
Real SSO/OIDC, real API Setu / DigiLocker, a full data-quality engine, real SMS/email, real Aadhaar, multi-tenant scale, production security hardening.

## DEMO STORY (3 minutes, everything must support this)
1. Citizen logs in (mock SSO) and applies once for a pension, giving consent once.
2. Connectors pull data from all three systems into one canonical format; the form is pre-filled.
3. The JSON workflow runs across departments; the tracker shows one timeline.
4. One application breaches its SLA and appears in the exception queue and dashboard.
5. Close with the "fields not retyped" counter and the audit log.

## BUILD ORDER (vertical: one ugly end-to-end path first, polish later)
Day 1: (1) mock departments [DONE] -> (2) connectors + canonical model -> (3) golden record + matching -> (4) consent + application -> (5) JSON workflow + tracker -> (6) audit log.
Day 2: (7) events + notifications -> (8) SLA breach, exception queue, 2 data-quality rules -> (9) dashboard + counter -> (10) citizen page + mock login -> (11) reset button + rehearsal -> (12) slides with future-scope slide.
Step 1 is already done: main.py (FastAPI mock departments: /mock/pension/beneficiaries/{pid}, /mock/ration/households) and data/municipal_residents.csv exist and work.

## HOW YOU MUST WORK
- One step at a time. Finish, let me test, confirm I'm happy, then move on. Ask at most ONE question per reply.
- Explain any new term in simple language first, then give the proper technical name (e.g., "golden record", "entity resolution", "dead-letter queue").
- Give complete, runnable code in small pieces I can test before continuing, with the exact file name for each piece and the command to run and test it.
- Give a time estimate per step and show a running checklist (done / left) at the end of each reply.
- For each step, say what to build for real, what to mock, and what to leave as future scope. Warn me immediately if I am over-building.
- I am comfortable with Python and FastAPI but weak at frontend, so keep the frontend simple and copy-paste ready.
- No fluff. Keep answers hackathon-ready and concise.

Start with Step 2: connectors and the canonical data model. First show me the canonical Person and Application models in plain terms, then the code for the three connectors.
## CURRENT STATUS (update after every step)
- [x] Step 1: mock departments
- [x] Step 2: connectors + canonical model
- [x] Step 3: golden record + matching
- [x] Step 4: consent + application
- [x] Step 5: JSON workflow + tracker
- [x] Step 6: audit log
(Day 2 steps 7-12 listed above)

## RULES FOR ANY AI TOOL
- Read this whole file before writing code.
- Do ONLY the step I name. Do not touch files from earlier steps unless I ask.
- Do not add libraries, frameworks, or features outside this file.
- Keep code in flat files next to main.py.