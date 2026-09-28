from datetime import datetime
from db import get_conn
from matching import score, LINK_THRESHOLD
from models import Person

MERGE_FIELDS = ["phone", "bank_account", "pension_status",
                "address", "ward", "annual_income", "family_members"]


def _now():
    return datetime.now().isoformat(timespec="seconds")


def resolve(person: Person) -> dict:
    """Link a per-system Person to a citizen (existing or new)."""
    conn = get_conn()
    try:
        s = person.source

        # 1. Already linked? Done.
        row = conn.execute(
            "SELECT citizen_id FROM source_links WHERE system=? AND external_id=?",
            (s.system, s.external_id)).fetchone()
        if row:
            return {"citizen_id": row["citizen_id"], "match_type": "EXISTING", "confidence": 1.0}

        # 2. Find best matching citizen
        best = None
        for c in conn.execute("SELECT * FROM citizens"):
            conf, mtype = score(person, c["full_name"], c["dob"])
            if best is None or conf > best[0]:
                best = (conf, mtype, c["citizen_id"])

        if best and best[0] >= LINK_THRESHOLD:
            conf, mtype, cid = best
            _merge(conn, cid, person)
        else:
            cur = conn.execute(
                """INSERT INTO citizens (full_name, dob, phone, bank_account, pension_status,
                   address, ward, annual_income, family_members, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (person.full_name, person.dob, person.phone, person.bank_account,
                 person.pension_status, person.address, person.ward,
                 person.annual_income, person.family_members, _now()))
            cid, conf, mtype = cur.lastrowid, 1.0, "NEW"

        # 3. Store the source-system link
        conn.execute(
            """INSERT INTO source_links (citizen_id, system, external_id,
               match_confidence, match_type, linked_at) VALUES (?,?,?,?,?,?)""",
            (cid, s.system, s.external_id, conf, mtype, _now()))
        conn.commit()
        return {"citizen_id": cid, "match_type": mtype, "confidence": conf}
    finally:
        conn.close()


def _merge(conn, cid: int, person: Person):
    """Fill gaps in the golden record; prefer the fuller name."""
    cur = conn.execute("SELECT * FROM citizens WHERE citizen_id=?", (cid,)).fetchone()
    if len(person.full_name) > len(cur["full_name"]):
        conn.execute("UPDATE citizens SET full_name=? WHERE citizen_id=?",
                     (person.full_name, cid))
    for f in MERGE_FIELDS:
        val = getattr(person, f)
        if val is not None and cur[f] is None:
            conn.execute(f"UPDATE citizens SET {f}=? WHERE citizen_id=?", (val, cid))


def get_citizen(cid: int) -> dict:
    conn = get_conn()
    try:
        c = conn.execute("SELECT * FROM citizens WHERE citizen_id=?", (cid,)).fetchone()
        links = conn.execute(
            "SELECT system, external_id, match_confidence, match_type "
            "FROM source_links WHERE citizen_id=? ORDER BY id", (cid,)).fetchall()
        return {**dict(c), "links": [dict(l) for l in links]}
    finally:
        conn.close()