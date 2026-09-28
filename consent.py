import json
from datetime import datetime, timedelta
from db import get_conn
import audit


class ConsentError(Exception):
    pass


# What each gated system reveals about a person
REQUIRED_FIELDS = {
    "MUNICIPAL": {"dob", "address", "ward"},
    "RATION": {"dob", "annual_income", "family_members"},
}
DEFAULT_FIELDS = ["dob", "address", "ward", "annual_income", "family_members"]


def _now():
    return datetime.now().isoformat(timespec="seconds")


def grant(citizen_id, purpose, fields=None, days=30, actor=None):
    fields = fields or DEFAULT_FIELDS
    expires = (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds")
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO consents (citizen_id, purpose, fields, expires_at, status, granted_at) "
            "VALUES (?,?,?,?, 'ACTIVE', ?)",
            (citizen_id, purpose, json.dumps(fields), expires, _now()))
        conn.commit()
        consent_id = cur.lastrowid
    finally:
        conn.close()
    audit.log(actor or f"citizen:{citizen_id}", "CONSENT_GRANTED", f"consent:{consent_id}",
              f"purpose={purpose} fields={','.join(fields)} expires={expires}")
    return consent_id


def revoke(consent_id, actor=None):
    conn = get_conn()
    try:
        row = conn.execute("SELECT citizen_id FROM consents WHERE consent_id=?",
                           (consent_id,)).fetchone()
        conn.execute("UPDATE consents SET status='REVOKED', revoked_at=? WHERE consent_id=?",
                     (_now(), consent_id))
        conn.commit()
    finally:
        conn.close()
    audit.log(actor or f"citizen:{row['citizen_id']}", "CONSENT_REVOKED", f"consent:{consent_id}")


def require(citizen_id, system, purpose):
    """The gate. Returns the consent_id used, or raises ConsentError."""
    needed = REQUIRED_FIELDS.get(system)
    if not needed:                       # home system (Pension): no cross-department sharing
        return None
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM consents WHERE citizen_id=? AND purpose=? "
            "AND status='ACTIVE' AND expires_at > ?",
            (citizen_id, purpose, _now())).fetchall()
    finally:
        conn.close()
    for r in rows:
        if needed <= set(json.loads(r["fields"])):
            return r["consent_id"]
    raise ConsentError(f"No active consent for {system} (missing, revoked, expired or fields not covered)")