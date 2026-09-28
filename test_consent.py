from db import reset_db
from gateway import login_identity, pull_all
from consent import grant, revoke, ConsentError
from applications import create_application
import audit

PURPOSE = "PENSION_APPLICATION"
reset_db()

cid = login_identity("PEN-1001")
print("Logged in as citizen", cid)

# 1. No consent -> must be refused
try:
    pull_all(cid, PURPOSE)
    print("1. FAIL: fetched without consent!")
except ConsentError as e:
    print("1. OK refused:", e)

# 2. Grant consent -> pull works, golden record fills up
consent_id = grant(cid, PURPOSE)
res = pull_all(cid, PURPOSE)
print("2. OK pulled:", {k: f"{v['match_type']} {v['confidence']}" for k, v in res.items()})

# 3. Application, pre-filled
app = create_application(cid)
print("3. Application", app.application_id, "| fields not retyped:", app.fields_autofilled)
print("   prefilled:", app.prefilled)

# 4. Revoke -> refused again
revoke(consent_id)
try:
    pull_all(cid, PURPOSE)
    print("4. FAIL: fetched after revoke!")
except ConsentError as e:
    print("4. OK refused after revoke")

# 5. Expired consent -> refused
grant(cid, PURPOSE, days=-1)
try:
    pull_all(cid, PURPOSE)
    print("5. FAIL: fetched with expired consent!")
except ConsentError:
    print("5. OK refused (expired)")

print("\nAUDIT LOG")
for r in audit.all_rows():
    print(f"{r['id']:>2} {r['actor']:16} {r['action']:20} {r['entity']:18} {r['detail']}")