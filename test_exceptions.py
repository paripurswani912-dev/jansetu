from datetime import datetime, timedelta
from db import reset_db, get_conn
from gateway import login_identity, pull_all, pull, ConnectorError
from consent import grant
from applications import create_application
import workflow, issues

reset_db()
PURPOSE = "PENSION_APPLICATION"

# --- 1. Normal happy path, then artificially breach the SLA ---
cid = login_identity("PEN-1001")
grant(cid, PURPOSE)
pull_all(cid, PURPOSE)
app = create_application(cid)
workflow.start(app.application_id)

conn = get_conn()
past = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
conn.execute("UPDATE workflow_steps SET due_at=? WHERE application_id=? AND status='ACTIVE'",
             (past, app.application_id))
conn.commit(); conn.close()

print("1. SLA check       :", workflow.check_sla())
print("   run again (no dup):", workflow.check_sla())

# --- 2. Connector failure -> retries -> dead-letter ---
try:
    pull(cid, "MUNICIPAL", "MUN-999", PURPOSE)   # doesn't exist
    print("2. FAIL: should have raised ConnectorError")
except ConnectorError as e:
    print("2. OK dead-lettered:", e)

# --- 3. Data quality: seed a bad phone directly, re-check ---
conn = get_conn()
conn.execute("UPDATE citizens SET phone='12345' WHERE citizen_id=?", (cid,))
conn.commit(); conn.close()
import quality
print("3. DQ issues        :", quality.check_citizen(cid))

print("\nOPEN EXCEPTIONS")
for x in issues.open_issues():
    print(f"  {x['id']:>2} {x['type']:17} app={x['application_id']} cit={x['citizen_id']} {x['detail']}")

print("\nDEAD LETTERS")
for d in issues.dead_letters():
    print(f"  {d['id']:>2} {d['system']:9} {d['external_id']:9} attempts={d['attempts']} {d['error']}")