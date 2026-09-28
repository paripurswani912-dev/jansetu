from typing import Optional
from pydantic import BaseModel


class SourceRef(BaseModel):
    system: str        # PENSION | MUNICIPAL | RATION
    external_id: str   # e.g. PEN-1001


class Person(BaseModel):
    source: SourceRef
    full_name: str
    name_key: str
    dob: Optional[str] = None          # ISO YYYY-MM-DD (None if unparseable)
    phone: Optional[str] = None
    bank_account: Optional[str] = None
    pension_status: Optional[str] = None
    address: Optional[str] = None
    ward: Optional[str] = None
    annual_income: Optional[int] = None
    family_members: Optional[int] = None


class Application(BaseModel):
    application_id: str
    citizen_id: int
    scheme: str = "PENSION"
    status: str = "SUBMITTED"
    prefilled: dict = {}
    fields_autofilled: int = 0
    created_at: str = ""