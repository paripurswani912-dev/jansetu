from fastapi import APIRouter, HTTPException
from workflow import get_tracker
import audit
router = APIRouter(prefix="/api")
@router.get("/audit")
def audit_rows():   
    return audit.all_rows()

@router.get("/audit/verify")
def audit_verify():
    return audit.verify()


@router.get("/tracker/{application_id}")
def tracker(application_id: str):
    t = get_tracker(application_id)
    if t is None:
        raise HTTPException(404, "Unknown application")
    return t