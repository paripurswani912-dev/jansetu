from fastapi import FastAPI, HTTPException, Response

app = FastAPI(title="SetuCare - Mock Departments")
from api import router
import subscribers
from fastapi.staticfiles import StaticFiles

app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException



@app.exception_handler(StarletteHTTPException)
async def custom_404(request, exc):
    if exc.status_code == 404:
        return FileResponse("static/404.html", status_code=404)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

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
    "PEN-1003": {"beneficiary_id": "PEN-1003", "full_name": "Lakshmi Bai",
                 "dob": "1955-01-20", "phone": "9876500003",
                 "bank_account": "HDFC0002345-778899", "pension_status": "not_enrolled"},
    "PEN-1004": {"beneficiary_id": "PEN-1004", "full_name": "Mohan Lal",
                 "dob": "1975-05-10", "phone": "9876500004",
                 "bank_account": "ICIC0003456-889900", "pension_status": "not_enrolled"},
    "PEN-1005": {"beneficiary_id": "PEN-1005", "full_name": "Geeta Sharma",
                 "dob": "1960-11-30", "phone": "98765",
                 "bank_account": "AXIS0004567-990011", "pension_status": "not_enrolled"},
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
  <household>
    <rationCardNo>BR-0101</rationCardNo>
    <headOfFamily>Lakshmi Bai</headOfFamily>
    <dateOfBirth>20-Jan-1955</dateOfBirth>
    <annualIncome>120000</annualIncome>
    <familyMembers>3</familyMembers>
  </household>
  <household>
    <rationCardNo>BR-0102</rationCardNo>
    <headOfFamily>Mohan Lal</headOfFamily>
    <dateOfBirth>10-May-1975</dateOfBirth>
    <annualIncome>200000</annualIncome>
    <familyMembers>5</familyMembers>
  </household>
  <household>
    <rationCardNo>BR-0103</rationCardNo>
    <headOfFamily>Geeta Sharma</headOfFamily>
    <dateOfBirth>30-Nov-1960</dateOfBirth>
    <annualIncome>150000</annualIncome>
    <familyMembers>2</familyMembers>
  </household>
</households>"""

@app.get("/mock/ration/households")
def ration_all():
    return Response(content=RATION_XML, media_type="application/xml")

# ---------- 3. MUNICIPAL: legacy CSV ----------
# No API at all. The connector reads data/municipal_residents.csv directly.