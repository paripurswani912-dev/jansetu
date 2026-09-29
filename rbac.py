from fastapi import HTTPException
from users import get_user
from gateway import login_identity


def resolve_user(user_id: str) -> dict:
    """Turns a mock login into {role, citizen_id}. For citizens, citizen_id comes
    from the SAME golden-record lookup as Step 4's login_identity — no separate
    session table needed, since it's idempotent."""
    u = get_user(user_id)
    if not u:
        raise HTTPException(401, "Unknown user")
    citizen_id = login_identity(u["pension_id"]) if u["role"] == "citizen" else None
    return {"user_id": user_id, "role": u["role"], "label": u["label"], "citizen_id": citizen_id}


def require_role(user: dict, *roles: str):
    if user["role"] not in roles:
        raise HTTPException(403, f"Role '{user['role']}' cannot do this (needs one of {roles})")