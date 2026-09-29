from db import reset_db
from gateway import login_identity, pull_all
from consent import grant
from applications import create_application
import workflow, subscribers, events

reset_db()
subscribers.register()

cid = login_identity("PEN-1001")
grant(cid, "PENSION_APPLICATION")
pull_all(cid, "PENSION_APPLICATION")
app = create_application(cid)
workflow.start(app.application_id)
workflow.decide(app.application_id, "officer:demo", True)

print("EVENTS")
for e in events.all_events():
    print(f"  {e['ts']} {e['type']:12} {e['application_id']} {e['detail']}")

print("\nNOTIFICATIONS (citizen", cid, ")")
for n in events.all_notifications(cid):
    print(f"  {n['ts']} {n['channel']:5} {n['message']}")