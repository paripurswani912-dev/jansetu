from connectors import CONNECTORS

for system, ext_id in [("PENSION", "PEN-1001"), ("MUNICIPAL", "MUN-77"), ("RATION", "BR-0099"),
                       ("PENSION", "PEN-1002"), ("MUNICIPAL", "MUN-78"), ("RATION", "BR-0100")]:
    p = CONNECTORS[system].fetch(ext_id)
    print(f"{system:9} {ext_id:9} -> {p.full_name!r:16} key={p.name_key!r:16} dob={p.dob} "
          f"income={p.annual_income} ward={p.ward}")