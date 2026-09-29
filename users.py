MOCK_USERS = {
    "ramesh":   {"label": "Ramesh Kumar (citizen)", "role": "citizen", "pension_id": "PEN-1001"},
    "sita":     {"label": "Sita Devi (citizen)",     "role": "citizen", "pension_id": "PEN-1002"},
    "clerk1":   {"label": "Priya — Clerk",           "role": "clerk"},
    "officer1": {"label": "Anil — Pension Officer",  "role": "officer"},
    "admin1":   {"label": "Admin",                   "role": "admin"},
}


def get_user(user_id: str):
    return MOCK_USERS.get(user_id)