"""Run this right after Reset demo, before presenting."""
from db import reset_db
import subscribers
subscribers.register()

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
reset_db()

# Ramesh applies and gets approved
r = client.post("/api/apply", json={"user_id": "ramesh"})
ramesh_app = r.json()["application_id"]
print("Ramesh applied:", ramesh_app)

client.post("/api/decide", json={"user_id": "officer1", "application_id": ramesh_app, "approve": True})
print("Ramesh approved")

# Sita applies and auto-rejects on income
r = client.post("/api/apply", json={"user_id": "sita"})
print("Sita applied:", r.json()["application_id"], "(auto-rejects on income)")

print("\nSeed complete. Dashboard and both citizen pages are demo-ready.")