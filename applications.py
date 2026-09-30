import json
from datetime import datetime
from db import get_conn
from golden import get_citizen
from models import Application
import audit
import quality

FORM_FIELDS = ["full_name", "dob", "phone", "bank_account",
               "address", "ward", "annual_income", "family_members"]


class DuplicateApplicationError(Exception):
    """Raised when a citizen already has an in-progress application for this scheme."""
    pass


def _existing_in_progress(citizen_id: int, scheme: str):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT application_id, status FROM applications "
            "WHERE citizen_id=? AND scheme=? AND status NOT IN ('APPROVED','REJECTED') "
            "ORDER BY created_at DESC LIMIT 1",
            (citizen_id, scheme)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_application(citizen_id: int, scheme: str = "PENSION") -> Application:
    existing = _existing_in_progress(citizen_id, scheme)
    if existing:
        raise DuplicateApplicationError(
            f"You already have an in-progress {scheme} application "
            f"({existing['application_id']}, status={existing['status']}). "
            f"Wait until it is approved or rejected before applying again."
        )

    c = get_citizen(citizen_id)
    prefilled = {f: c[f] for f in FORM_FIELDS if c.get(f) is not None}
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

    quality.check_citizen(citizen_id, app_id)

    audit.log(f"citizen:{citizen_id}", "APPLICATION_CREATED", app_id,
              f"scheme={scheme} autofilled={len(prefilled)}")
    return Application(application_id=app_id, citizen_id=citizen_id, scheme=scheme,
                       status="SUBMITTED", prefilled=prefilled,
                       fields_autofilled=len(prefilled), created_at=now)