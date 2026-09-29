from datetime import datetime
from db import get_conn

_SUBSCRIBERS = {}   # event type -> list of functions


def _now():
    return datetime.now().isoformat(timespec="seconds")


def subscribe(event_type, fn):
    _SUBSCRIBERS.setdefault(event_type, []).append(fn)


def publish(event_type, application_id=None, citizen_id=None, detail=""):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO events (ts, application_id, citizen_id, type, detail) VALUES (?,?,?,?,?)",
            (_now(), application_id, citizen_id, event_type, detail))
        conn.commit()
    finally:
        conn.close()

    for fn in _SUBSCRIBERS.get(event_type, []):
        fn(application_id=application_id, citizen_id=citizen_id, detail=detail)


def notify(citizen_id, channel, message):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO notifications (ts, citizen_id, channel, message) VALUES (?,?,?,?)",
            (_now(), citizen_id, channel, message))
        conn.commit()
    finally:
        conn.close()


def all_events():
    conn = get_conn()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id")]
    finally:
        conn.close()


def all_notifications(citizen_id=None):
    conn = get_conn()
    try:
        if citizen_id is None:
            rows = conn.execute("SELECT * FROM notifications ORDER BY id")
        else:
            rows = conn.execute("SELECT * FROM notifications WHERE citizen_id=? ORDER BY id", (citizen_id,))
        return [dict(r) for r in rows]
    finally:
        conn.close()