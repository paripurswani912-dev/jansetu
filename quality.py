import re
from datetime import date
from golden import get_citizen
import issues

PHONE_RE = re.compile(r"^\d{10}$")


def check_citizen(citizen_id, application_id=None):
    """Rule 1: phone must be 10 digits. Rule 2: DOB valid + age 0-120. Returns issues found."""
    c = get_citizen(citizen_id)
    found = []

    if c.get("phone") is not None and not PHONE_RE.match(str(c["phone"])):
        msg = f"phone '{c['phone']}' is not 10 digits"
        issues.raise_issue("DATA_QUALITY", msg, application_id, citizen_id)
        found.append(msg)

    dob = c.get("dob")
    if dob is None:
        msg = "date of birth missing or unparseable"
        issues.raise_issue("DATA_QUALITY", msg, application_id, citizen_id)
        found.append(msg)
    else:
        try:
            d = date.fromisoformat(dob)
            today = date.today()
            age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
            if not (0 <= age <= 120):
                msg = f"implausible age {age} from dob {dob}"
                issues.raise_issue("DATA_QUALITY", msg, application_id, citizen_id)
                found.append(msg)
        except ValueError:
            msg = f"invalid dob format: {dob}"
            issues.raise_issue("DATA_QUALITY", msg, application_id, citizen_id)
            found.append(msg)
    return found