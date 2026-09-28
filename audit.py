import hashlib
from datetime import datetime
from db import get_conn

GENESIS = "0" * 64   # "previous hash" of the very first row


def _hash(prev_hash, ts, actor, action, entity, detail):
    payload = "|".join([prev_hash, ts or "", actor or "", action or "", entity or "", detail or ""])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def log(actor: str, action: str, entity: str = "", detail: str = ""):
    """Append one audit row, chained to the previous row's hash."""
    ts = datetime.now().isoformat(timespec="seconds")
    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")   # lock so two writers can't share the same prev_hash
        last = conn.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
        prev = last["hash"] if last and last["hash"] else GENESIS
        h = _hash(prev, ts, actor, action, entity, detail)
        conn.execute(
            "INSERT INTO audit_log (ts, actor, action, entity, detail, prev_hash, hash) "
            "VALUES (?,?,?,?,?,?,?)",
            (ts, actor, action, entity, detail, prev, h))
        conn.commit()
    finally:
        conn.close()


def all_rows():
    conn = get_conn()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM audit_log ORDER BY id")]
    finally:
        conn.close()


def verify():
    """Recompute the whole chain. Returns where it first breaks, if anywhere."""
    rows = all_rows()
    prev = GENESIS
    for r in rows:
        if r["prev_hash"] != prev:
            return {"valid": False, "checked": len(rows), "broken_at": r["id"],
                    "reason": "chain link broken: an earlier row was deleted or replaced"}
        if _hash(prev, r["ts"], r["actor"], r["action"], r["entity"], r["detail"]) != r["hash"]:
            return {"valid": False, "checked": len(rows), "broken_at": r["id"],
                    "reason": "row contents were modified"}
        prev = r["hash"]
    return {"valid": True, "checked": len(rows), "broken_at": None, "reason": "", "head": prev}