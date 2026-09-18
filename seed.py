"""
seed.py
Creates baseline data: super admin, principal, classes, sections,
subjects, teachers, students, parent, assignments, and a sample
timetable.

Run once after creating the schema:
    python seed.py
"""
from datetime import date

from utils.supabase_client import table
from utils.password_utils import hash_password
from utils.roll_number import generate_roll_number


def upsert_user(roll, password, role, name, phone=""):
    """Create user if missing; otherwise update password hash."""
    existing = table("users").select("*").eq("roll_number", roll).limit(1).execute().data
    if existing:
        table("users").update({"password_hash": hash_password(password)}).eq("id", existing[0]["id"]).execute()
        return existing[0]
    return table("users").insert({
        "roll_number": roll,
        "password_hash": hash_password(password),
        "role": role,
        "name": name,
        "phone": phone,
    }).execute().data[0]


def main():
    print("Seeding Super Admin...")
    sa = upsert_user("SA-2025-0001", "admin123", "super_admin", "Super Admin")

    print("Seeding Principal...")
    upsert_user("P-2025-0001", "principal123", "principal", "Principal Khan")

    print("Seeding classes...")
    classes = {}
    for name in ["9th", "10th"]:
        existing = table("classes").select("*").eq("name", name).execute().data
        if existing:
            classes[name] = existing[0]
        else:
            classes[name] = table("classes").insert({"name": name}).execute().data[0]

    print("Seeding sections...")
    sections = {}
    def ensure_section(class_name, sec_name):
        key = f"{class_name}-{sec_name}"
        if key in sections:
            return sections[key]
        existing = table("sections").select("*").eq(
            "class_id", classes[class_name]["id"]
        ).eq("name", sec_name).execute().data
        if existing:
            sections[key] = existing[0]
        else:
            sections[key] = table("sections").insert({
                "class_id": classes[class_name]["id"],
                "name": sec_name,
            }).execute().data[0]
        return sections[key]

    ensure_section("9th", "A")
    ensure_section("9th", "B")
    ensure_section("10th", "A")

    print("Seeding subjects...")
    subjects = {}
    for name, code in [("Computer", "CS"), ("English", "EN"), ("Math", "MA"), ("Physics", "PH")]:
        existing = table("subjects").select("*").eq("name", name).execute().data
        if existing:
            subjects[name] = existing[0]
        else:
            subjects[name] = table("subjects").insert({"name": name, "code": code}).execute().data[0]

    print("Seeding teachers...")
    ali = upsert_user("T-2025-0001", "teacher123", "teacher", "Ali", "0300-1111111")
    sara = upsert_user("T-2025-0002", "teacher123", "teacher", "Sara", "0300-2222222")

    for t in (ali, sara):
        ex = table("teachers").select("*").eq("user_id", t["id"]).execute().data
        if not ex:
            table("teachers").insert({
                "user_id": t["id"],
                "qualification": "M.Sc",
                "joining_date": str(date.today()),
            }).execute()

    print("Seeding assignments...")
    def ensure_assignment(teacher_id, class_name, section_name, subject_name):
        payload = {
            "teacher_user_id": teacher_id,
            "class_id": classes[class_name]["id"],
            "section_id": sections[f"{class_name}-{section_name}"]["id"],
            "subject_id": subjects[subject_name]["id"],
        }
        ex = table("teacher_assignments").select("*").eq(
            "teacher_user_id", teacher_id
        ).eq("class_id", payload["class_id"]).eq(
            "section_id", payload["section_id"]
        ).eq("subject_id", payload["subject_id"]).execute().data
        if not ex:
            table("teacher_assignments").insert(payload).execute()

    ensure_assignment(ali["id"], "9th", "A", "Computer")
    ensure_assignment(ali["id"], "9th", "B", "Computer")
    ensure_assignment(sara["id"], "9th", "A", "English")

    print("Seeding students...")
    ahmed = upsert_user("S-2025-0001", "student123", "student", "Ahmed")
    bilal = upsert_user("S-2025-0002", "student123", "student", "Bilal")

    for u, roll_in_class in ((ahmed, 1), (bilal, 2)):
        ex = table("students").select("*").eq("user_id", u["id"]).execute().data
        if not ex:
            table("students").insert({
                "user_id": u["id"],
                "class_id": classes["9th"]["id"],
                "section_id": sections["9th-A"]["id"],
                "roll_no_in_class": roll_in_class,
                "guardian_name": "Mr. Guardian",
                "guardian_phone": "0300-9999999",
                "address": "Sample Address",
            }).execute()

    print("Seeding parent...")
    parent = upsert_user("PT-2025-0001", "parent123", "parent", "Mr. Father")
    table("students").update({"parent_user_id": parent["id"]}).eq("user_id", ahmed["id"]).execute()

    print("Seeding timetable (9th-A Monday)...")
    ex = table("timetable").select("*").eq(
        "class_id", classes["9th"]["id"]
    ).eq("section_id", sections["9th-A"]["id"]).execute().data
    if not ex:
        table("timetable").insert([
            {
                "class_id": classes["9th"]["id"],
                "section_id": sections["9th-A"]["id"],
                "subject_id": subjects["Computer"]["id"],
                "teacher_user_id": ali["id"],
                "day": "Monday",
                "period_no": 1,
                "start_time": "08:00",
                "end_time": "08:45",
            },
            {
                "class_id": classes["9th"]["id"],
                "section_id": sections["9th-A"]["id"],
                "subject_id": subjects["English"]["id"],
                "teacher_user_id": sara["id"],
                "day": "Monday",
                "period_no": 2,
                "start_time": "09:00",
                "end_time": "09:45",
            },
        ]).execute()

    print("\n✅ Seeding complete!\n")
    print("Login credentials:")
    print("  Super Admin : SA-2025-0001 / admin123")
    print("  Principal   : P-2025-0001 / principal123")
    print("  Teacher Ali : T-2025-0001 / teacher123")
    print("  Teacher Sara: T-2025-0002 / teacher123")
    print("  Student     : S-2025-0001 / student123")
    print("  Parent      : PT-2025-0001 / parent123")


if __name__ == "__main__":
    main()