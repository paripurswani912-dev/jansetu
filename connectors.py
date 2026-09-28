import csv
import xml.etree.ElementTree as ET
import requests

from models import Person, SourceRef
from normalize import clean_name, name_key, to_iso

BASE_URL = "http://127.0.0.1:8000"   # your mock departments (same server)


class Connector:
    system = ""

    def fetch(self, external_id: str) -> Person:
        raise NotImplementedError


class PensionConnector(Connector):
    """Modern REST/JSON."""
    system = "PENSION"

    def fetch(self, external_id: str) -> Person:
        r = requests.get(f"{BASE_URL}/mock/pension/beneficiaries/{external_id}", timeout=5)
        r.raise_for_status()
        d = r.json()
        return Person(
            source=SourceRef(system=self.system, external_id=d["beneficiary_id"]),
            full_name=clean_name(d["full_name"]),
            name_key=name_key(d["full_name"]),
            dob=to_iso(d["dob"], "%Y-%m-%d"),
            phone=d.get("phone"),
            bank_account=d.get("bank_account"),
            pension_status=d.get("pension_status"),
        )


class MunicipalConnector(Connector):
    """Legacy CSV file."""
    system = "MUNICIPAL"
    path = "data/municipal_residents.csv"

    def fetch(self, external_id: str) -> Person:
        with open(self.path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["RES_NO"].strip() == external_id:
                    return Person(
                        source=SourceRef(system=self.system, external_id=external_id),
                        full_name=clean_name(row["NAME"]),
                        name_key=name_key(row["NAME"]),
                        dob=to_iso(row["BIRTH_DT"], "%d/%m/%Y"),
                        address=row["ADDR"].strip(),
                        ward=row["WARD"].strip(),
                    )
        raise LookupError(f"{external_id} not found in municipal CSV")


class RationConnector(Connector):
    """Old XML service."""
    system = "RATION"

    def fetch(self, external_id: str) -> Person:
        r = requests.get(f"{BASE_URL}/mock/ration/households", timeout=5)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        # Find the element that holds this rationCardNo, tolerant of XML nesting
        for el in root.iter():
            if el.findtext("rationCardNo", "").strip() == external_id:
                head = el.findtext("headOfFamily", "")
                return Person(
                    source=SourceRef(system=self.system, external_id=external_id),
                    full_name=clean_name(head),
                    name_key=name_key(head),
                    dob=to_iso(el.findtext("dateOfBirth", ""), "%d-%b-%Y"),
                    annual_income=int(el.findtext("annualIncome", "0")),
                    family_members=int(el.findtext("familyMembers", "0")),
                )
        raise LookupError(f"{external_id} not found in ration XML")


CONNECTORS = {c.system: c() for c in (PensionConnector, MunicipalConnector, RationConnector)}