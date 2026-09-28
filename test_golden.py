from connectors import CONNECTORS
from db import reset_db, get_conn
from golden import resolve, get_citizen

reset_db()

for system, ext_id in [("PENSION", "PEN-1001"), ("MUNICIPAL", "MUN-77"), ("RATION", "BR-0099"),
                       ("PENSION", "PEN-1002"), ("MUNICIPAL", "MUN-78"), ("RATION", "BR-0100")]:
    p = CONNECTORS[system].fetch(ext_id)
    r = resolve(p)
    print(f"{ext_id:9} -> citizen {r['citizen_id']}  {r['match_type']:8} conf={r['confidence']}")

print()
conn = get_conn()
ids = [r["citizen_id"] for r in conn.execute("SELECT citizen_id FROM citizens")]
conn.close()
for cid in ids:
    c = get_citizen(cid)
    print(f"Citizen {cid}: {c['full_name']}, dob={c['dob']}, phone={c['phone']}, "
          f"ward={c['ward']}, income={c['annual_income']}")
    for l in c["links"]:
        print(f"    {l['system']:9} {l['external_id']:9} {l['match_type']:6} {l['match_confidence']}")