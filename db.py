import os
import sqlite3

DB_PATH = "jansetu.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS citizens (
    citizen_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name      TEXT NOT NULL,
    dob            TEXT,
    phone          TEXT,
    bank_account   TEXT,
    pension_status TEXT,
    address        TEXT,
    ward           TEXT,
    annual_income  INTEGER,
    family_members INTEGER,
    created_at     TEXT
);

CREATE TABLE IF NOT EXISTS source_links (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    citizen_id       INTEGER NOT NULL,
    system           TEXT NOT NULL,
    external_id      TEXT NOT NULL,
    match_confidence REAL,
    match_type       TEXT,
    linked_at        TEXT,
    UNIQUE(system, external_id)
);

CREATE TABLE IF NOT EXISTS consents (
    consent_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    citizen_id  INTEGER NOT NULL,
    purpose     TEXT NOT NULL,
    fields      TEXT NOT NULL,        -- JSON list
    expires_at  TEXT NOT NULL,
    status      TEXT NOT NULL,        -- ACTIVE | REVOKED
    granted_at  TEXT,
    revoked_at  TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    application_id    TEXT PRIMARY KEY,   -- APP-0001
    citizen_id        INTEGER NOT NULL,
    scheme            TEXT,
    status            TEXT,
    prefilled         TEXT,               -- JSON
    fields_autofilled INTEGER,
    created_at        TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT,
    actor     TEXT,
    action    TEXT,
    entity    TEXT,
    detail    TEXT,
    prev_hash TEXT,     -- filled in Step 6
    hash      TEXT      -- filled in Step 6
);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT NOT NULL,
    seq            INTEGER NOT NULL,
    step_id        TEXT NOT NULL,
    label          TEXT,
    department     TEXT,
    status         TEXT NOT NULL,   -- PENDING | ACTIVE | PASSED | FAILED | SKIPPED
    sla_hours      INTEGER,
    started_at     TEXT,
    due_at         TEXT,
    completed_at   TEXT,
    result         TEXT,
    spec           TEXT             -- JSON copy of the step definition
);

CREATE TABLE IF NOT EXISTS timeline (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT NOT NULL,
    ts             TEXT,
    department     TEXT,
    event          TEXT,
    detail         TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT,
    application_id TEXT,
    citizen_id     INTEGER,
    type           TEXT,
    detail         TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT,
    citizen_id INTEGER,
    channel    TEXT,     -- SMS | EMAIL
    message    TEXT
);

CREATE TABLE IF NOT EXISTS exceptions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT,
    type           TEXT,     -- SLA_BREACH | DATA_QUALITY | CONNECTOR_FAILURE
    application_id TEXT,
    citizen_id     INTEGER,
    detail         TEXT,
    status         TEXT      -- OPEN | RESOLVED
);

CREATE TABLE IF NOT EXISTS dead_letter (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT,
    system      TEXT,
    external_id TEXT,
    purpose     TEXT,
    error       TEXT,
    attempts    INTEGER
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def reset_db():
    """'Reset demo' = delete the file and recreate it."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()