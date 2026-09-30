import json
from datetime import datetime
from db import get_conn
from golden import get_citizen
from models import Application
import audit
import quality

FORM_FIELDS = ["full_name", "dob", "phone", "bank_account",
               "address", "ward", "annual_income", "family_members"]

def create_application(citizen_id: int, scheme: str = "PENSION") -> Application:
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT application_id FROM applications WHERE citizen_id=? AND scheme=? "
            "AND status NOT IN ('APPROVED','REJECTED')", (citizen_id, scheme)).fetchone()
    finally:
        conn.close()
    if existing:
        raise ValueError(f"Already has an in-progress {scheme} application: {existing['application_id']}")

def create_application(citizen_id: int, scheme: str = "PENSION") -> Application:
    c = get_citizen(citizen_id)
    prefilled = {f: c[f] for f in FORM_FIELDS if c.get(f) is not None}   # what the citizen did NOT retype
    quality.check_citizen(citizen_id)
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_conn()
    try:
        n = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        app_id = f"APP-{n + 1:04d}"
        conn.execute(
            "INSERT INTO applications VALUES (?,?,?,?,?,?,?)",
            (app_id, citizen_id, scheme, "SUBMITTED", json.dumps(prefilled), len(prefilled), now))
        conn.commit()
    finally:
        conn.close()
    audit.log(f"citizen:{citizen_id}", "APPLICATION_CREATED", app_id,
              f"scheme={scheme} autofilled={len(prefilled)}")
    return Application(application_id=app_id, citizen_id=citizen_id, scheme=scheme,
                       status="SUBMITTED", prefilled=prefilled,
                       fields_autofilled=len(prefilled), created_at=now)