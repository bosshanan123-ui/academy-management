"""
routes/teacher.py
Teacher dashboard, attendance, marks, timetable, ID card.
"""
from datetime import date

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)

from utils.supabase_client import table
from utils.decorators import role_required

teacher_bp = Blueprint("teacher", __name__)


# =====================================================
# DASHBOARD
# =====================================================
@teacher_bp.route("/dashboard")
@role_required("teacher")
def dashboard():
    tid = session["user_id"]
    assigns = _safe_select("teacher_assignments", teacher_user_id=tid)
    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")

    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}

    for a in assigns:
        a["class_name"] = cmap.get(a["class_id"], "-")
        a["section_name"] = smap.get(a["section_id"], "-")
        a["subject_name"] = submap.get(a["subject_id"], "-")

    today_name = date.today().strftime("%A")
    today = _safe_select("timetable", teacher_user_id=tid, day=today_name)
    for t in today:
        t["class_name"] = cmap.get(t["class_id"], "-")
        t["section_name"] = smap.get(t["section_id"], "-")
        t["subject_name"] = submap.get(t["subject_id"], "-")

    notices = _safe_select("notices")

    return render_template(
        "teacher/dashboard.html",
        assignments=assigns,
        today_schedule=today,
        today_name=today_name,
        notices=notices,
    )


# =====================================================
# ATTENDANCE
# =====================================================
@teacher_bp.route(
    "/attendance/<int:class_id>/<int:section_id>/<int:subject_id>",
    methods=["GET", "POST"],
)
@role_required("teacher")
def attendance(class_id, section_id, subject_id):
    tid = session["user_id"]

    if not _is_assigned(tid, class_id, section_id, subject_id):
        flash("You are not assigned to this class/section/subject.", "error")
        return redirect(url_for("teacher.dashboard"))

    if request.method == "POST":
        today = str(date.today())
        students = _students_in(class_id, section_id)

        if not students:
            flash("No students found in this class/section.", "error")
            return redirect(url_for("teacher.dashboard"))

        saved = 0
        failed = 0

        for s in students:
            user_id = s.get("user_id")
            if not user_id:
                failed += 1
                continue

            status = request.form.get(f"status_{user_id}")
            if status not in ("P", "A", "L"):
                continue

            try:
                table("attendance").delete() \
                    .eq("student_user_id", user_id) \
                    .eq("subject_id", subject_id) \
                    .eq("date", today).execute()

                table("attendance").insert({
                    "student_user_id": user_id,
                    "class_id": class_id,
                    "section_id": section_id,
                    "subject_id": subject_id,
                    "teacher_user_id": tid,
                    "date": today,
                    "status": status,
                }).execute()
                saved += 1
            except Exception as e:
                failed += 1
                print(f"Attendance insert error for user {user_id}: {e}")

        if saved > 0:
            flash(f"Attendance saved for {saved} student(s).", "success")
        if failed > 0:
            flash(f"Failed for {failed} student(s). Check logs.", "warning")

        return redirect(url_for("teacher.dashboard"))

    students = _students_in(class_id, section_id)
    subject = _get_one("subjects", subject_id)

    return render_template(
        "teacher/attendance.html",
        students=students,
        subject=subject,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
    )


# =====================================================
# MARKS
# =====================================================
@teacher_bp.route(
    "/marks/<int:class_id>/<int:section_id>/<int:subject_id>",
    methods=["GET", "POST"],
)
@role_required("teacher")
def marks(class_id, section_id, subject_id):
    tid = session["user_id"]

    if not _is_assigned(tid, class_id, section_id, subject_id):
        flash("You are not assigned to this class/section/subject.", "error")
        return redirect(url_for("teacher.dashboard"))

    if request.method == "POST":
        exam_type = (request.form.get("exam_type") or "Monthly").strip()
        try:
            total = int(request.form.get("total_marks") or 100)
        except ValueError:
            total = 100

        students = _students_in(class_id, section_id)
        if not students:
            flash("No students found in this class/section.", "error")
            return redirect(url_for("teacher.dashboard"))

        saved = 0
        for s in students:
            user_id = s.get("user_id")
            if not user_id:
                continue

            obtained = request.form.get(f"marks_{user_id}")
            if obtained is None or obtained == "":
                continue

            try:
                obtained_int = int(obtained)
            except ValueError:
                continue

            try:
                table("marks").insert({
                    "student_user_id": user_id,
                    "subject_id": subject_id,
                    "exam_type": exam_type,
                    "total_marks": total,
                    "obtained_marks": obtained_int,
                }).execute()
                saved += 1
            except Exception as e:
                print(f"Marks insert error for user {user_id}: {e}")

        flash(f"Marks saved for {saved} student(s).", "success")
        return redirect(url_for("teacher.dashboard"))

    students = _students_in(class_id, section_id)
    subject = _get_one("subjects", subject_id)

    return render_template(
        "teacher/marks.html",
        students=students,
        subject=subject,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
    )


# =====================================================
# TIMETABLE
# =====================================================
@teacher_bp.route("/timetable")
@role_required("teacher")
def timetable():
    tid = session["user_id"]
    entries = _safe_select("timetable", teacher_user_id=tid)
    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")

    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}

    for e in entries:
        e["class_name"] = cmap.get(e["class_id"], "-")
        e["section_name"] = smap.get(e["section_id"], "-")
        e["subject_name"] = submap.get(e["subject_id"], "-")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    grid = {d: [e for e in entries if e["day"] == d] for d in days}

    return render_template("teacher/timetable.html", grid=grid, days=days)


# =====================================================
# ID CARD
# =====================================================
@teacher_bp.route("/id-card")
@role_required("teacher")
def id_card():
    """Teacher ID card — view + print."""
    uid = session["user_id"]

    # Get user
    user_rows = _safe_select("users", id=uid)
    user = user_rows[0] if user_rows else {}

    # Get teacher profile
    teacher_rows = _safe_select("teachers", user_id=uid)
    teacher = teacher_rows[0] if teacher_rows else {}

    # Academy info
    academy = {
        "name": "Academy Management System",
        "tagline": "Excellence in Education",
        "address": "123 Education Street, City",
        "phone": "+92 300 0000000",
        "website": "academy-ms.app",
        "session": "2025-2026",
    }

    return render_template(
        "id_cards/teacher_card.html",
        user=user,
        teacher=teacher,
        academy=academy,
    )


# =====================================================
# HELPERS
# =====================================================
def _safe_select(table_name, **filters):
    """Select rows from a table with optional equality filters."""
    try:
        q = table(table_name).select("*")
        for k, v in filters.items():
            q = q.eq(k, v)
        return q.execute().data or []
    except Exception as e:
        print(f"_safe_select error ({table_name}): {e}")
        return []


def _get_one(table_name, pk):
    """Fetch a single row by primary key."""
    try:
        res = table(table_name).select("*").eq("id", pk).limit(1).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"_get_one error ({table_name}, id={pk}): {e}")
        return {}


def _is_assigned(teacher_id, class_id, section_id, subject_id):
    """Check if teacher is assigned to this class/section/subject."""
    try:
        res = table("teacher_assignments").select("id").eq(
            "teacher_user_id", teacher_id
        ).eq("class_id", class_id).eq(
            "section_id", section_id
        ).eq("subject_id", subject_id).limit(1).execute()
        return bool(res.data)
    except Exception as e:
        print(f"_is_assigned error: {e}")
        return False


def _students_in(class_id, section_id):
    """Return list of student dicts for class+section."""
    try:
        profiles = table("students").select("*").eq(
            "class_id", class_id
        ).eq("section_id", section_id).execute().data or []

        if not profiles:
            return []

        user_ids = [p["user_id"] for p in profiles if p.get("user_id")]
        if not user_ids:
            return []

        users = table("users").select("*").in_("id", user_ids).execute().data or []
        umap = {u["id"]: u for u in users}

        out = []
        for p in profiles:
            u = umap.get(p.get("user_id"))
            if not u:
                continue

            merged = {
                "user_id": u["id"],
                "id": u["id"],
                "roll_number": u.get("roll_number"),
                "name": u.get("name"),
                "role": u.get("role"),
                "is_active": u.get("is_active"),
                "phone": u.get("phone"),
                "roll_no_in_class": p.get("roll_no_in_class"),
            }
            out.append(merged)

        return sorted(out, key=lambda x: x.get("roll_no_in_class") or 9999)
    except Exception as e:
        print(f"_students_in error: {e}")
        return []
