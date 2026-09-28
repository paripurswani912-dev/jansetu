from db import reset_db
from gateway import login_identity, pull_all
from consent import grant
from applications import create_application
import workflow

PURPOSE = "PENSION_APPLICATION"
reset_db()


def run(pension_id):
    cid = login_identity(pension_id)
    grant(cid, PURPOSE)
    pull_all(cid, PURPOSE)
    app = create_application(cid)
    workflow.start(app.application_id)
    return app.application_id


def show(app_id):
    t = workflow.get_tracker(app_id)
    a = t["application"]
    print(f"\n{app_id}  citizen {a['citizen_id']}  status={a['status']}")
    for s in t["steps"]:
        print(f"  {s['seq']}. {s['step_id']:14} {s['department']:9} {s['status']:8} {s['result'] or ''}")
    print("  timeline:")
    for e in t["timeline"]:
        print(f"    {e['ts']}  {e['department']:9} {e['event']:17} {e['detail']}")


a1 = run("PEN-1001")                       # Ramesh
show(a1)                                   # expect: waiting at approve
workflow.decide(a1, "officer:demo", True)
show(a1)                                   # expect: APPROVED

a2 = run("PEN-1002")                       # Sita
show(a2)                                   # expect: REJECTED at income