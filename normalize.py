import re
from datetime import datetime
from typing import Optional


def clean_name(raw: str) -> str:
    """'R. KUMAR' -> 'R Kumar'"""
    s = re.sub(r"[^\w\s]", " ", raw or "")
    return " ".join(s.split()).title()


def name_key(raw: str) -> str:
    """Lowercase key used for matching in Step 3."""
    return clean_name(raw).lower()


def to_iso(raw: str, fmt: str) -> Optional[str]:
    """Convert a date string to ISO. Returns None if invalid
    (Step 8's data-quality rule will flag None)."""
    try:
        return datetime.strptime(raw.strip(), fmt).date().isoformat()
    except (ValueError, AttributeError):
        return None