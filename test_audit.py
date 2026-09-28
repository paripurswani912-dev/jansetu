from db import reset_db, get_conn
from gateway import login_identity, pull_all
from consent import grant
from applications import create_application
import workflow, audit

reset_db()
PURPOSE = "PENSION_APPLICATION"
cid = login_identity("PEN-1001")
grant(cid, PURPOSE)
pull_all(cid, PURPOSE)
app = create_application(cid)
workflow.start(app.application_id)
workflow.decide(app.application_id, "officer:demo", True)

print("1. Fresh log      :", audit.verify())

# 2. Tamper: quietly change what a row says
conn = get_conn()
original = conn.execute("SELECT detail FROM audit_log WHERE id=3").fetchone()["detail"]
conn.execute("UPDATE audit_log SET detail='nothing to see here' WHERE id=3")
conn.commit(); conn.close()
print("2. After edit     :", audit.verify())

# 3. Undo the edit -> chain valid again
conn = get_conn()
conn.execute("UPDATE audit_log SET detail=? WHERE id=3", (original,))
conn.commit(); conn.close()
print("3. Edit undone    :", audit.verify()["valid"])

# 4. Tamper: delete a row
conn = get_conn()
conn.execute("DELETE FROM audit_log WHERE id=5")
conn.commit(); conn.close()
print("4. After deletion :", audit.verify())