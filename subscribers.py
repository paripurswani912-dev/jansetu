import events

MESSAGES = {
    "AGE_VERIFIED": "Your age has been verified with Municipal records.",
    "INCOME_VERIFIED": "Your income has been verified with Ration records.",
    "APPROVED": "Your pension application has been approved.",
    "REJECTED": "Your pension application was rejected. Check the tracker for details.",
}


def _on_step_event(application_id, citizen_id, detail):
    # detail carries the step's on_pass value, set by _notify_step below
    pass


def _notify(application_id, citizen_id, detail):
    msg = MESSAGES.get(detail, f"Update on {application_id}: {detail}")
    events.notify(citizen_id, "SMS", msg)


def register():
    events.subscribe("STEP_RESULT", _notify)