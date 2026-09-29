from datetime import datetime
from db import get_conn


def _now():
    return datetime.now().isoformat(timespec="seconds")


def raise_issue(type_, detail, application_id=None, citizen_id=None):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO exceptions (ts, type, application_id, citizen_id, detail, status) "
            "VALUES (?,?,?,?,?, 'OPEN')",
            (_now(), type_, application_id, citizen_id, detail))
        conn.commit()
    finally:
        conn.close()


def open_issues():
    conn = get_conn()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM exceptions WHERE status='OPEN' ORDER BY id")]
    finally:
        conn.close()


def resolve(issue_id):
    conn = get_conn()
    try:
        conn.execute("UPDATE exceptions SET status='RESOLVED' WHERE id=?", (issue_id,))
        conn.commit()
    finally:
        conn.close()


def record_dead_letter(system, external_id, purpose, error, attempts):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO dead_letter (ts, system, external_id, purpose, error, attempts) VALUES (?,?,?,?,?,?)",
            (_now(), system, external_id, purpose, error, attempts))
        conn.commit()
    finally:
        conn.close()


def dead_letters():
    conn = get_conn()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM dead_letter ORDER BY id")]
    finally:
        conn.close()