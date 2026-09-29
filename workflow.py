import json
import os
from datetime import datetime, timedelta, date

from db import get_conn
from golden import get_citizen
import audit
import events

WORKFLOW_DIR = "workflows"


# ---- tiny DB helpers (short-lived connections avoid SQLite "database is locked") ----
def _exec(sql, params=()):
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _q(sql, params=()):
    conn = get_conn()
    try:
        return [dict(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


def _iso(dt):
    return dt.isoformat(timespec="seconds")


def _timeline(app_id, dept, event, detail=""):
    _exec("INSERT INTO timeline (application_id, ts, department, event, detail) VALUES (?,?,?,?,?)",
          (app_id, _iso(datetime.now()), dept, event, detail))


# ---- rules: each returns (passed, explanation) ----
def _age(dob_iso):
    d, t = date.fromisoformat(dob_iso), date.today()
    return t.year - d.year - ((t.month, t.day) < (d.month, d.day))


def rule_min_age(c, value):
    if not c.get("dob"):
        return False, "date of birth missing"
    a = _age(c["dob"])
    return a >= value, f"age {a} (minimum {value})"


def rule_max_income(c, value):
    inc = c.get("annual_income")
    if inc is None:
        return False, "income missing"
    return inc <= value, f"income {inc} (limit {value})"


RULES = {"min_age": rule_min_age, "max_income": rule_max_income}   # "manual" is handled below


def load_workflow(scheme):
    with open(os.path.join(WORKFLOW_DIR, f"{scheme.lower()}.json"), encoding="utf-8") as f:
        return json.load(f)


# ---- engine ----
def start(app_id):
    app = _q("SELECT * FROM applications WHERE application_id=?", (app_id,))[0]
    wf = load_workflow(app["scheme"])
    for i, s in enumerate(wf["steps"], 1):
        _exec("INSERT INTO workflow_steps (application_id, seq, step_id, label, department, "
              "status, sla_hours, spec) VALUES (?,?,?,?,?, 'PENDING', ?, ?)",
              (app_id, i, s["id"], s["label"], s["department"], s["sla_hours"], json.dumps(s)))
    _timeline(app_id, "PENSION", "SUBMITTED", "Application submitted by citizen (pre-filled)")
    audit.log("system:workflow", "WORKFLOW_STARTED", app_id, f"{wf['name']} steps={len(wf['steps'])}")
    advance(app_id)


def _finish(app_id, step, passed, detail, actor="system:workflow"):
    spec = json.loads(step["spec"])
    _exec("UPDATE workflow_steps SET status=?, completed_at=?, result=? WHERE id=?",
          ("PASSED" if passed else "FAILED", _iso(datetime.now()), detail, step["id"]))
    app = _q("SELECT citizen_id FROM applications WHERE application_id=?", (app_id,))[0]
    if passed:
        _exec("UPDATE applications SET status=? WHERE application_id=?", (spec["on_pass"], app_id))
        _timeline(app_id, step["department"], spec["on_pass"], f"{step['label']}: {detail}")
        audit.log(actor, "STEP_PASSED", app_id, f"{step['step_id']} | {detail}")
        events.publish("STEP_RESULT", app_id, app["citizen_id"], spec["on_pass"])
    else:
        _exec("UPDATE applications SET status='REJECTED' WHERE application_id=?", (app_id,))
        _exec("UPDATE workflow_steps SET status='SKIPPED' WHERE application_id=? AND status='PENDING'",
              (app_id,))
        _timeline(app_id, step["department"], "REJECTED", f"{step['label']} failed: {detail}")
        audit.log(actor, "STEP_FAILED", app_id, f"{step['step_id']} | {detail}")
        events.publish("STEP_RESULT", app_id, app["citizen_id"], "REJECTED")

def advance(app_id):
    """Run steps until the application finishes or waits for a human."""
    while True:
        app = _q("SELECT * FROM applications WHERE application_id=?", (app_id,))[0]
        if app["status"] in ("APPROVED", "REJECTED"):
            return
        nxt = _q("SELECT * FROM workflow_steps WHERE application_id=? "
                 "AND status IN ('PENDING','ACTIVE') ORDER BY seq LIMIT 1", (app_id,))
        if not nxt:
            return
        step = nxt[0]
        rule = json.loads(step["spec"])["rule"]

        if step["status"] == "PENDING":                      # activate: start the SLA clock
            now = datetime.now()
            _exec("UPDATE workflow_steps SET status='ACTIVE', started_at=?, due_at=? WHERE id=?",
                  (_iso(now), _iso(now + timedelta(hours=step["sla_hours"])), step["id"]))
            if rule["type"] == "manual":
                _timeline(app_id, step["department"], "AWAITING_OFFICER",
                          f"{step['label']} pending (SLA {step['sla_hours']}h)")

        if rule["type"] == "manual":                         # wait for decide()
            return

        passed, detail = RULES[rule["type"]](get_citizen(app["citizen_id"]), rule["value"])
        _finish(app_id, step, passed, detail)


def decide(app_id, officer, approve, note=""):
    """Officer approves or rejects. (Role check is added in Step 10.)"""
    rows = _q("SELECT * FROM workflow_steps WHERE application_id=? AND status='ACTIVE' "
              "AND spec LIKE '%\"manual\"%'", (app_id,))
    if not rows:
        raise ValueError("No step is awaiting officer approval")
    _finish(app_id, rows[0], approve,
            note or ("Approved" if approve else "Rejected") + f" by {officer}", actor=officer)


def get_tracker(app_id):
    apps = _q("SELECT * FROM applications WHERE application_id=?", (app_id,))
    if not apps:
        return None
    app = apps[0]
    app["prefilled"] = json.loads(app["prefilled"] or "{}")
    steps = _q("SELECT seq, step_id, label, department, status, sla_hours, due_at, completed_at, result "
               "FROM workflow_steps WHERE application_id=? ORDER BY seq", (app_id,))
    timeline = _q("SELECT ts, department, event, detail FROM timeline "
                  "WHERE application_id=? ORDER BY id", (app_id,))
    return {"application": app, "steps": steps, "timeline": timeline}