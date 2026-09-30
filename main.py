from fastapi import FastAPI, HTTPException, Response

app = FastAPI(title="JanSetu - Mock Departments")
from api import router
import subscribers
from fastapi.staticfiles import StaticFiles

app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def custom_404(request, exc):
    if exc.status_code == 404:
        return FileResponse("static/404.html", status_code=404)
    raise exc

@app.get("/")
def root():
    return RedirectResponse("/static/login.html")

subscribers.register()

# ---------- 1. PENSION: modern REST/JSON ----------
PENSION = {
    "PEN-1001": {"beneficiary_id": "PEN-1001", "full_name": "Ramesh Kumar",
                 "dob": "1958-03-14", "phone": "9876500001",
                 "bank_account": "SBIN0001234-556677", "pension_status": "not_enrolled"},
    "PEN-1002": {"beneficiary_id": "PEN-1002", "full_name": "Sita Devi",
                 "dob": "1961-07-02", "phone": "9876500002",
                 "bank_account": "PUNB0004321-112233", "pension_status": "not_enrolled"},
}

@app.get("/mock/pension/beneficiaries/{pid}")
def pension_get(pid: str):
    if pid not in PENSION:
        raise HTTPException(404, "beneficiary not found")
    return PENSION[pid]

# ---------- 2. RATION CARD: old XML service ----------
RATION_XML = """<?xml version="1.0"?>
<households>
  <household>
    <rationCardNo>BR-0099</rationCardNo>
    <headOfFamily>Ramesh Kumar</headOfFamily>
    <dateOfBirth>14-Mar-1958</dateOfBirth>
    <annualIncome>90000</annualIncome>
    <familyMembers>4</familyMembers>
  </household>
  <household>
    <rationCardNo>BR-0100</rationCardNo>
    <headOfFamily>Sita Devi</headOfFamily>
    <dateOfBirth>02-Jul-1961</dateOfBirth>
    <annualIncome>310000</annualIncome>
    <familyMembers>2</familyMembers>
  </household>
</households>"""

@app.get("/mock/ration/households")
def ration_all():
    return Response(content=RATION_XML, media_type="application/xml")

# ---------- 3. MUNICIPAL: legacy CSV ----------
# No API at all. The connector will read data/municipal_residents.csv directly.

@app.get("/")
def health():
    return {"status": "mock departments running"}