"""
utils/roll_number.py
Auto-generates roll numbers of the form PREFIX-YYYY-NNNN.
Serial resets per role per year.
"""
from datetime import datetime

from utils.supabase_client import table

PREFIX_MAP = {
    "super_admin": "SA",
    "principal": "P",
    "teacher": "T",
    "student": "S",
    "parent": "PT",
}


def generate_roll_number(role: str, year: int | None = None) -> str:
    """
    Generate the next roll number for a given role.

    Args:
        role: one of super_admin, principal, teacher, student, parent.
        year: academic year (defaults to current year).

    Returns:
        Roll number string, e.g. 'T-2025-0001'.
    """
    if role not in PREFIX_MAP:
        raise ValueError(f"Unknown role: {role}")

    year = year or datetime.utcnow().year
    prefix = PREFIX_MAP[role]
    year_str = str(year)

    # Fetch all roll numbers for this role
    res = table("users").select("roll_number").eq("role", role).execute()
    rows = res.data or []

    max_serial = 0
    for row in rows:
        rn = row.get("roll_number") or ""
        parts = rn.split("-")
        if len(parts) != 3:
            continue
        if parts[0] != prefix:
            continue
        if parts[1] != year_str:
            continue
        try:
            serial = int(parts[2])
            if serial > max_serial:
                max_serial = serial
        except ValueError:
            continue

    next_serial = max_serial + 1
    return f"{prefix}-{year_str}-{next_serial:04d}"