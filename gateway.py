from connectors import CONNECTORS
from consent import require, ConsentError
from golden import resolve
from db import get_conn
import audit
import issues

# MOCK crosswalk: a real system would search each department by name + DOB
CROSSWALK = {
    "PEN-1001": {"MUNICIPAL": "MUN-77", "RATION": "BR-0099"},
    "PEN-1002": {"MUNICIPAL": "MUN-78", "RATION": "BR-0100"},
    "PEN-1003": {"MUNICIPAL": "MUN-79", "RATION": "BR-0101"},
    "PEN-1004": {"MUNICIPAL": "MUN-80", "RATION": "BR-0102"},
    "PEN-1005": {"MUNICIPAL": "MUN-81", "RATION": "BR-0103"},
}


def login_identity(pension_id: str) -> int:
    """Mock SSO result: the citizen's home-system profile becomes their citizen record."""
    person = CONNECTORS["PENSION"].fetch(pension_id)
    r = resolve(person)
    audit.log(f"citizen:{r['citizen_id']}", "LOGIN", f"PENSION:{pension_id}")
    return r["citizen_id"]


class ConnectorError(Exception):
    pass


def pull(citizen_id, system, external_id, purpose, max_retries=3):
    actor = f"citizen:{citizen_id}"
    try:
        consent_id = require(citizen_id, system, purpose)
    except ConsentError as e:
        audit.log("system:gateway", "FETCH_REFUSED", f"{system}:{external_id}", str(e))
        raise

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            person = CONNECTORS[system].fetch(external_id)
            break
        except Exception as e:
            last_err = e
            audit.log("system:gateway", "FETCH_RETRY", f"{system}:{external_id}",
                      f"attempt {attempt}/{max_retries}: {e}")
    else:
        issues.record_dead_letter(system, external_id, purpose, str(last_err), max_retries)
        issues.raise_issue("CONNECTOR_FAILURE",
                           f"{system}:{external_id} failed after {max_retries} attempts: {last_err}",
                           None, citizen_id)
        audit.log("system:gateway", "FETCH_DEAD_LETTER", f"{system}:{external_id}", str(last_err))
        raise ConnectorError(str(last_err))

    r = resolve(person)
    audit.log("system:gateway", "CONSENT_USED", f"consent:{consent_id}",
              f"{system}:{external_id} -> citizen {r['citizen_id']} ({r['match_type']} {r['confidence']})")
    return r


def pull_all(citizen_id, purpose):
    """Pull every other department for this citizen (uses the crosswalk)."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT external_id FROM source_links WHERE citizen_id=? AND system='PENSION'",
                           (citizen_id,)).fetchone()
    finally:
        conn.close()
    results = {}
    for system, ext_id in CROSSWALK[row["external_id"]].items():
        results[system] = pull(citizen_id, system, ext_id, purpose)
    return results