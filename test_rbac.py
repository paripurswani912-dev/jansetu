from fastapi.testclient import TestClient
from db import reset_db
import subscribers

reset_db()
subscribers.register()

from main import app
client = TestClient(app)

# 1. Ramesh applies
r = client.post("/api/apply", json={"user_id": "ramesh"})
print("1. apply:", r.status_code, r.json())
app_id = r.json()["application_id"]

# 2. Sita (citizen) tries to approve -> must be refused
r = client.post("/api/decide", json={"user_id": "sita", "application_id": app_id, "approve": True})
print("2. citizen decide (expect 403):", r.status_code)

# 3. Officer approves -> allowed
r = client.post("/api/decide", json={"user_id": "officer1", "application_id": app_id, "approve": True})
print("3. officer decide:", r.status_code, r.json())

# 4. Sita tries to view Ramesh's tracker -> must be refused
r = client.get(f"/api/tracker/{app_id}", params={"user_id": "sita"})
print("4. wrong citizen tracker (expect 403):", r.status_code)

# 5. Ramesh views his own tracker -> allowed
r = client.get(f"/api/tracker/{app_id}", params={"user_id": "ramesh"})
print("5. own tracker:", r.status_code, r.json()["application"]["status"])

# 6. Citizen tries the dashboard -> must be refused
r = client.get("/api/dashboard", params={"user_id": "ramesh"})
print("6. citizen dashboard (expect 403):", r.status_code)

# 7. Clerk views the dashboard -> allowed
r = client.get("/api/dashboard", params={"user_id": "clerk1"})
print("7. clerk dashboard:", r.status_code)