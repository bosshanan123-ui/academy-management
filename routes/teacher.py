"""
routes/teacher.py
Teacher dashboard, attendance, marks, timetable.
"""
from datetime import date

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, abort
)

from utils.supabase_client import table
from utils.decorators import role_required

teacher_bp = Blueprint("teacher", __name__)


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


@teacher_bp.route("/attendance/<int:class_id>/<int:section_id>/<int:subject_id>",
                  methods=["GET", "POST"])
@role_required("teacher")
def attendance(class_id, section_id, subject_id):
    tid = session["user_id"]
    if not _is_assigned(tid, class_id, section_id, subject_id):
        flash("You are not assigned to this class/section/subject.", "error")
        return redirect(url_for("teacher.dashboard"))

    if request.method == "POST":
        today = str(date.today())
        students = _students_in(class_id, section_id)
        for s in students:
            status = request.form.get(f"status_{s['user_id']}")
            if status in ("P", "A", "L"):
                # delete existing for today/subject then insert
                try:
                    table("attendance").delete() \
                        .eq("student_user_id", s["user_id"]) \
                        .eq("subject_id", subject_id) \
                        .eq("date", today).execute()
                    table("attendance").insert({
                        "student_user_id": s["user_id"],
                        "class_id": class_id,
                        "section_id": section_id,
                        "subject_id": subject_id,
                        "teacher_user_id": tid,
                        "date": today,
                        "status": status,
                    }).execute()
                except Exception:
                    pass
        flash("Attendance saved.", "success")
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


@teacher_bp.route("/marks/<int:class_id>/<int:section_id>/<int:subject_id>",
                  methods=["GET", "POST"])
@role_required("teacher")
def marks(class_id, section_id, subject_id):
    tid = session["user_id"]
    if not _is_assigned(tid, class_id, section_id, subject_id):
        flash("You are not assigned to this class/section/subject.", "error")
        return redirect(url_for("teacher.dashboard"))

    if request.method == "POST":
        exam_type = (request.form.get("exam_type") or "Monthly").strip()
        total = int(request.form.get("total_marks") or 100)
        students = _students_in(class_id, section_id)
        for s in students:
            obtained = request.form.get(f"marks_{s['user_id']}")
            if obtained is None or obtained == "":
                continue
            try:
                table("marks").insert({
                    "student_user_id": s["user_id"],
                    "subject_id": subject_id,
                    "exam_type": exam_type,
                    "total_marks": total,
                    "obtained_marks": int(obtained),
                }).execute()
            except Exception:
                pass
        flash("Marks saved.", "success")
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


# ---------- helpers ----------
def _safe_select(table_name, **filters):
    try:
        q = table(table_name).select("*")
        for k, v in filters.items():
            q = q.eq(k, v)
        return q.execute().data or []
    except Exception:
        return []


def _get_one(table_name, pk):
    try:
        res = table(table_name).select("*").eq("id", pk).limit(1).execute()
        return res.data[0] if res.data else {}
    except Exception:
        return {}


def _is_assigned(tid, class_id, section_id, subject_id):
    try:
        res = table("teacher_assignments").select("id").eq(
            "teacher_user_id", tid
        ).eq("class_id", class_id).eq(
            "section_id", section_id
        ).eq("subject_id", subject_id).limit(1).execute()
        return bool(res.data)
    except Exception:
        return False


def _students_in(class_id, section_id):
    """Return list of student user dicts for class+section."""
    try:
        profiles = table("students").select("*").eq(
            "class_id", class_id
        ).eq("section_id", section_id).execute().data or []
        user_ids = [p["user_id"] for p in profiles]
        if not user_ids:
            return []
        users = table("users").select("*").in_("id", user_ids).execute().data or []
        umap = {u["id"]: u for u in users}
        out = []
        for p in profiles:
            u = umap.get(p["user_id"])
            if u:
                u = dict(u)
                u["roll_no_in_class"] = p.get("roll_no_in_class")
                out.append(u)
        return sorted(out, key=lambda x: x.get("roll_no_in_class") or 9999)
    except Exception:
        return []