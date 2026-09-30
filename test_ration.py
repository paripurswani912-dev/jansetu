# add to a scratch cell or new test_ration.py
from db import reset_db
import subscribers
subscribers.register()
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
reset_db()
r = client.post("/api/apply", json={"user_id": "ramesh", "scheme": "ration_renewal"})
print(r.json())