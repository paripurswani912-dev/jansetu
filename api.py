from fastapi import APIRouter, HTTPException
from workflow import get_tracker
import audit
import events


router = APIRouter(prefix="/api")

@router.get("/audit")
def audit_rows():   
    return audit.all_rows()

@router.get("/audit/verify")
def audit_verify():
    return audit.verify()


@router.get("/notifications/{citizen_id}")
def notifications(citizen_id: int):
    return events.all_notifications(citizen_id)

@router.get("/events")
def all_events():
    return events.all_events()

@router.get("/tracker/{application_id}")
def tracker(application_id: str):
    t = get_tracker(application_id)
    if t is None:
        raise HTTPException(404, "Unknown application")
    return t
@router.get("/exceptions")
def exceptions_list():
    return issues.open_issues()

@router.get("/dead-letter")
def dead_letter_list():
    return issues.dead_letters()

@router.get("/check-sla")
def run_sla_check():
    return {"newly_breached": workflow.check_sla()}

