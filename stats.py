from db import get_conn


def _q(sql, params=()):
    conn = get_conn()
    try:
        return [dict(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


def counts_by_status():
    rows = _q("SELECT status, COUNT(*) AS n FROM applications GROUP BY status")
    return {r["status"]: r["n"] for r in rows}


def sla_compliance():
    rows = _q("SELECT status, due_at, completed_at FROM workflow_steps "
              "WHERE status IN ('PASSED','FAILED') AND due_at IS NOT NULL AND completed_at IS NOT NULL")
    if not rows:
        return {"percent": None, "on_time": 0, "total": 0}
    on_time = sum(1 for r in rows if r["completed_at"] <= r["due_at"])
    return {"percent": round(100 * on_time / len(rows), 1), "on_time": on_time, "total": len(rows)}


def avg_processing_hours():
    rows = _q("SELECT a.created_at AS started, MAX(t.ts) AS ended "
              "FROM applications a JOIN timeline t ON t.application_id = a.application_id "
              "WHERE a.status IN ('APPROVED','REJECTED') GROUP BY a.application_id")
    if not rows:
        return None
    from datetime import datetime
    diffs = [(datetime.fromisoformat(r["ended"]) - datetime.fromisoformat(r["started"])).total_seconds() / 3600
             for r in rows]
    return round(sum(diffs) / len(diffs), 3)


def connector_health():
    systems = ["PENSION", "MUNICIPAL", "RATION"]
    health = {}
    for s in systems:
        n = _q("SELECT COUNT(*) AS n FROM dead_letter WHERE system=?", (s,))[0]["n"]
        health[s] = "DEGRADED" if n > 0 else "OK"
    return health


def fields_not_retyped_total():
    row = _q("SELECT COALESCE(SUM(fields_autofilled), 0) AS n FROM applications")[0]
    return row["n"]


def duplicates_avoided():
    row = _q("SELECT COUNT(*) AS n FROM source_links WHERE match_type IN ('EXACT','FUZZY')")[0]
    return row["n"]


def exception_queue_summary():
    rows = _q("SELECT type, COUNT(*) AS n FROM exceptions WHERE status='OPEN' GROUP BY type")
    return {r["type"]: r["n"] for r in rows}


def dashboard():
    return {
        "counts_by_status": counts_by_status(),
        "sla_compliance": sla_compliance(),
        "avg_processing_hours": avg_processing_hours(),
        "connector_health": connector_health(),
        "fields_not_retyped_total": fields_not_retyped_total(),
        "duplicates_avoided": duplicates_avoided(),
        "open_exceptions": exception_queue_summary(),
        "open_exceptions_total": sum(exception_queue_summary().values()),
    }