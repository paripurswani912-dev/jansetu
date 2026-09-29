from datetime import datetime, timedelta
from db import reset_db, get_conn
from gateway import login_identity, pull_all
from consent import grant
from applications import create_application
import workflow, stats

reset_db()
PURPOSE = "PENSION_APPLICATION"


def run(pid):
    cid = login_identity(pid)
    grant(cid, PURPOSE)
    pull_all(cid, PURPOSE)
    app = create_application(cid)
    workflow.start(app.application_id)
    return app.application_id, cid


a1, cid1 = run("PEN-1001")
workflow.decide(a1, "officer:demo", True)      # Ramesh: APPROVED

a2, cid2 = run("PEN-1002")                      # Sita: REJECTED at income (auto)

# Breach a step so SLA compliance < 100%
conn = get_conn()
past = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
conn.execute("UPDATE workflow_steps SET due_at=? WHERE application_id=? AND status='ACTIVE'",
             (past, a1))
conn.commit(); conn.close()
workflow.check_sla()

import pprint
pprint.pprint(stats.dashboard())