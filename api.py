from typing import Optional
from fastapi import APIRouter, HTTPException, Body

import workflow
import audit
import events
import issues
import stats
from workflow import get_tracker
from users import MOCK_USERS
from rbac import resolve_user, require_role
from consent import grant
from gateway import pull_all
from applications import create_application
from db import get_conn

router = APIRouter(prefix="/api")


# ---------- auth ----------
@router.get("/users")
def list_users():
    return [{"user_id": k, "label": v["label"], "role": v["role"]} for k, v in MOCK_USERS.items()]


@router.get("/me")
def me(user_id: str):
    return resolve_user(user_id)


# ---------- citizen actions ----------
@router.post("/apply")
def apply(user_id: str = Body(...), scheme: str = Body("PENSION")):
    user = resolve_user(user_id)
    require_role(user, "citizen")
    cid = user["citizen_id"]
    grant(cid, "PENSION_APPLICATION")
    pull_all(cid, "PENSION_APPLICATION")
    app = create_application(cid, scheme)
    workflow.start(app.application_id)
    return {"application_id": app.application_id, "fields_autofilled": app.fields_autofilled}


@router.get("/my-applications")
def my_applications(user_id: str):
    user = resolve_user(user_id)
    require_role(user, "citizen")
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT application_id, status, created_at FROM applications "
            "WHERE citizen_id=? ORDER BY created_at", (user["citizen_id"],)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/notifications/{citizen_id}")
def notifications(citizen_id: int, user_id: str):
    user = resolve_user(user_id)
    if user["role"] == "citizen" and user["citizen_id"] != citizen_id:
        raise HTTPException(403, "Not your notifications")
    return events.all_notifications(citizen_id)


# ---------- tracker (citizen: own only; staff: any) ----------
@router.get("/tracker/{application_id}")
def tracker(application_id: str, user_id: Optional[str] = None):
    t = get_tracker(application_id)
    if t is None:
        raise HTTPException(404, "Unknown application")
    if user_id:
        user = resolve_user(user_id)
        if user["role"] == "citizen" and t["application"]["citizen_id"] != user["citizen_id"]:
            raise HTTPException(403, "Not your application")
    return t


# ---------- officer actions ----------
@router.post("/decide")
def decide(user_id: str = Body(...), application_id: str = Body(...),
           approve: bool = Body(...), note: str = Body("")):
    user = resolve_user(user_id)
    require_role(user, "officer", "admin")
    workflow.decide(application_id, f"{user['role']}:{user_id}", approve, note)
    return {"ok": True}


# ---------- staff-only views ----------
STAFF = ("clerk", "officer", "admin")


@router.get("/dashboard")
def dashboard(user_id: str):
    require_role(resolve_user(user_id), *STAFF)
    return stats.dashboard()


@router.get("/exceptions")
def exceptions_list(user_id: str):
    require_role(resolve_user(user_id), *STAFF)
    return issues.open_issues()


@router.get("/dead-letter")
def dead_letter_list(user_id: str):
    require_role(resolve_user(user_id), *STAFF)
    return issues.dead_letters()


@router.get("/check-sla")
def run_sla_check(user_id: str):
    require_role(resolve_user(user_id), *STAFF)
    return {"newly_breached": workflow.check_sla()}


@router.get("/audit")
def audit_rows(user_id: str):
    require_role(resolve_user(user_id), *STAFF)
    return audit.all_rows()


@router.get("/audit/verify")
def audit_verify(user_id: str):
    require_role(resolve_user(user_id), *STAFF)
    return audit.verify()


@router.get("/events")
def all_events(user_id: str):
    require_role(resolve_user(user_id), *STAFF)
    return events.all_events()