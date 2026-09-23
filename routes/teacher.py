"""
routes/teacher.py
Teacher dashboard, attendance, marks, timetable, ID card.
"""
from datetime import date, timedelta

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
    recent_attendance = _recent_attendance(tid, limit=5)
    recent_marks = _recent_marks(tid, limit=5)

    return render_template(
        "teacher/dashboard.html",
        assignments=assigns,
        today_schedule=today,
        today_name=today_name,
        notices=notices,
        recent_attendance=recent_attendance,
        recent_marks=recent_marks,
    )


# =====================================================
# ATTENDANCE — Take
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
            flash("No students found.", "error")
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
                table("attendance").delete().eq("student_user_id", user_id).eq("subject_id", subject_id).eq("date", today).execute()
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

        if saved > 0:
            flash(f"Attendance saved for {saved} student(s).", "success")
        if failed > 0:
            flash(f"Failed for {failed}.", "warning")
        return redirect(url_for("teacher.dashboard"))

    students = _students_in(class_id, section_id)
    subject = _get_one("subjects", subject_id)
    cls = _get_one("classes", class_id)
    sec = _get_one("sections", section_id)
    existing = _existing_attendance(str(date.today()), class_id, section_id, subject_id)

    return render_template(
        "teacher/attendance.html",
        students=students,
        subject=subject,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        existing=existing,
        class_name=cls.get("name", "-"),
        section_name=sec.get("name", "-"),
        today_date=date.today().strftime("%d %B %Y (%A)"),
    )


# =====================================================
# ATTENDANCE — History
# =====================================================
@teacher_bp.route("/attendance/history")
@role_required("teacher")
def attendance_history():
    tid = session["user_id"]
    from_date = (request.args.get("from") or "").strip()
    to_date = (request.args.get("to") or "").strip()
    class_filter = (request.args.get("class_id") or "").strip()
    subject_filter = (request.args.get("subject_id") or "").strip()

    if not from_date and not to_date:
        to_date = str(date.today())
        from_date = str(date.today() - timedelta(days=30))

    classes = _safe_select("classes")
    subjects = _safe_select("subjects")
    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in _safe_select("sections")}
    submap = {s["id"]: s["name"] for s in subjects}

    try:
        all_records = table("attendance").select("*").eq("teacher_user_id", tid).order("date", desc=True).execute().data or []
    except Exception:
        all_records = []

    filtered = []
    for r in all_records:
        d = str(r.get("date") or "")
        if from_date and d < from_date:
            continue
        if to_date and d > to_date:
            continue
        if class_filter and str(r.get("class_id")) != class_filter:
            continue
        if subject_filter and str(r.get("subject_id")) != subject_filter:
            continue
        filtered.append(r)

    sessions = {}
    for r in filtered:
        key = (str(r.get("date")), r.get("class_id"), r.get("section_id"), r.get("subject_id"))
        if key not in sessions:
            sessions[key] = {
                "date": r.get("date"),
                "class_id": r.get("class_id"),
                "section_id": r.get("section_id"),
                "subject_id": r.get("subject_id"),
                "class_name": cmap.get(r.get("class_id"), "-"),
                "section_name": smap.get(r.get("section_id"), "-"),
                "subject_name": submap.get(r.get("subject_id"), "-"),
                "P": 0, "A": 0, "L": 0, "total": 0,
            }
        status = r.get("status")
        sessions[key][status] = sessions[key].get(status, 0) + 1
        sessions[key]["total"] += 1

    session_list = []
    for s in sessions.values():
        t = s["total"] or 1
        s["percent"] = round(s["P"] * 100 / t, 1)
        session_list.append(s)
    session_list.sort(key=lambda x: (str(x["date"]), x["class_name"]), reverse=True)

    total_sessions = len(session_list)
    total_students = sum(s["total"] for s in session_list)
    total_present = sum(s["P"] for s in session_list)
    avg_percent = round(total_present * 100 / total_students, 1) if total_students else 0

    return render_template(
        "teacher/attendance_history.html",
        sessions=session_list,
        classes=classes,
        subjects=subjects,
        from_date=from_date,
        to_date=to_date,
        class_filter=class_filter,
        subject_filter=subject_filter,
        stats={"total_sessions": total_sessions, "total_students": total_students, "total_present": total_present, "avg_percent": avg_percent},
    )


@teacher_bp.route("/attendance/view/<date_str>/<int:class_id>/<int:section_id>/<int:subject_id>")
@role_required("teacher")
def attendance_view(date_str, class_id, section_id, subject_id):
    tid = session["user_id"]
    if not _is_assigned(tid, class_id, section_id, subject_id):
        flash("Not assigned.", "error")
        return redirect(url_for("teacher.attendance_history"))

    try:
        records = table("attendance").select("*").eq("teacher_user_id", tid).eq("class_id", class_id).eq("section_id", section_id).eq("subject_id", subject_id).eq("date", date_str).execute().data or []
    except Exception:
        records = []

    student_ids = [r["student_user_id"] for r in records]
    students_map = {}
    if student_ids:
        try:
            users = table("users").select("*").in_("id", student_ids).execute().data or []
            students_map = {u["id"]: u for u in users}
        except Exception:
            pass

    enriched = []
    for r in records:
        u = students_map.get(r["student_user_id"], {})
        enriched.append({
            "student_name": u.get("name", "-"),
            "roll_number": u.get("roll_number", "-"),
            "status": r.get("status", "-"),
        })
    enriched.sort(key=lambda x: x["roll_number"])

    cls = _get_one("classes", class_id)
    sec = _get_one("sections", section_id)
    sub = _get_one("subjects", subject_id)

    p = sum(1 for e in enriched if e["status"] == "P")
    ab = sum(1 for e in enriched if e["status"] == "A")
    lv = sum(1 for e in enriched if e["status"] == "L")

    return render_template(
        "teacher/attendance_view.html",
        date_str=date_str,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        class_name=cls.get("name", "-"),
        section_name=sec.get("name", "-"),
        subject_name=sub.get("name", "-"),
        records=enriched,
        stats={"P": p, "A": ab, "L": lv, "total": len(enriched)},
    )


@teacher_bp.route("/attendance/edit/<date_str>/<int:class_id>/<int:section_id>/<int:subject_id>", methods=["GET", "POST"])
@role_required("teacher")
def attendance_edit(date_str, class_id, section_id, subject_id):
    tid = session["user_id"]
    if not _is_assigned(tid, class_id, section_id, subject_id):
        flash("Not assigned.", "error")
        return redirect(url_for("teacher.attendance_history"))

    if request.method == "POST":
        students = _students_in(class_id, section_id)
        saved = 0
        for s in students:
            user_id = s.get("user_id")
            if not user_id:
                continue
            status = request.form.get(f"status_{user_id}")
            if status not in ("P", "A", "L"):
                continue
            try:
                table("attendance").delete().eq("student_user_id", user_id).eq("subject_id", subject_id).eq("date", date_str).execute()
                table("attendance").insert({
                    "student_user_id": user_id,
                    "class_id": class_id,
                    "section_id": section_id,
                    "subject_id": subject_id,
                    "teacher_user_id": tid,
                    "date": date_str,
                    "status": status,
                }).execute()
                saved += 1
            except Exception:
                pass
        flash(f"Updated for {saved}.", "success")
        return redirect(url_for("teacher.attendance_view", date_str=date_str, class_id=class_id, section_id=section_id, subject_id=subject_id))

    students = _students_in(class_id, section_id)
    existing = {}
    try:
        recs = table("attendance").select("*").eq("class_id", class_id).eq("section_id", section_id).eq("subject_id", subject_id).eq("date", date_str).execute().data or []
        for r in recs:
            existing[r["student_user_id"]] = r["status"]
    except Exception:
        pass

    cls = _get_one("classes", class_id)
    sec = _get_one("sections", section_id)
    sub = _get_one("subjects", subject_id)

    return render_template(
        "teacher/attendance_edit.html",
        date_str=date_str,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        class_name=cls.get("name", "-"),
        section_name=sec.get("name", "-"),
        subject_name=sub.get("name", "-"),
        students=students,
        existing=existing,
    )


# =====================================================
# MARKS
# =====================================================
@teacher_bp.route("/marks/<int:class_id>/<int:section_id>/<int:subject_id>", methods=["GET", "POST"])
@role_required("teacher")
def marks(class_id, section_id, subject_id):
    tid = session["user_id"]
    if not _is_assigned(tid, class_id, section_id, subject_id):
        flash("Not assigned.", "error")
        return redirect(url_for("teacher.dashboard"))

    if request.method == "POST":
        exam_type = (request.form.get("exam_type") or "Monthly").strip()
        try:
            total = int(request.form.get("total_marks") or 100)
        except ValueError:
            total = 100

        students = _students_in(class_id, section_id)
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
            except Exception:
                pass
        flash(f"Marks saved for {saved}.", "success")
        return redirect(url_for("teacher.dashboard"))

    students = _students_in(class_id, section_id)
    subject = _get_one("subjects", subject_id)
    cls = _get_one("classes", class_id)
    sec = _get_one("sections", section_id)

    return render_template(
        "teacher/marks.html",
        students=students,
        subject=subject,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        class_name=cls.get("name", "-"),
        section_name=sec.get("name", "-"),
    )


# =====================================================
# MARKS — History
# =====================================================
@teacher_bp.route("/marks/history")
@role_required("teacher")
def marks_history():
    tid = session["user_id"]
    class_filter = (request.args.get("class_id") or "").strip()
    subject_filter = (request.args.get("subject_id") or "").strip()
    exam_filter = (request.args.get("exam_type") or "").strip()

    classes = _safe_select("classes")
    subjects = _safe_select("subjects")
    cmap = {c["id"]: c["name"] for c in classes}
    submap = {s["id"]: s["name"] for s in subjects}

    assigns = _safe_select("teacher_assignments", teacher_user_id=tid)
    valid = {(a["class_id"], a["subject_id"]) for a in assigns}

    try:
        all_marks = table("marks").select("*").order("created_at", desc=True).limit(500).execute().data or []
    except Exception:
        all_marks = []

    profiles = _safe_select("students")
    pmap = {p["user_id"]: p for p in profiles}

    filtered = []
    for m in all_marks:
        sid = m.get("student_user_id")
        sub_id = m.get("subject_id")
        profile = pmap.get(sid)
        if not profile:
            continue
        cid = profile.get("class_id")
        if (cid, sub_id) not in valid:
            continue
        if class_filter and str(cid) != class_filter:
            continue
        if subject_filter and str(sub_id) != subject_filter:
            continue
        if exam_filter and m.get("exam_type") != exam_filter:
            continue
        filtered.append(m)

    sessions = {}
    for m in filtered:
        sid = m.get("student_user_id")
        profile = pmap.get(sid, {})
        cid = profile.get("class_id")
        key = (m.get("exam_type"), cid, m.get("subject_id"))
        if key not in sessions:
            sessions[key] = {
                "exam_type": m.get("exam_type"),
                "class_id": cid,
                "class_name": cmap.get(cid, "-"),
                "subject_id": m.get("subject_id"),
                "subject_name": submap.get(m.get("subject_id"), "-"),
                "count": 0,
                "total_obtained": 0,
                "total_possible": 0,
                "latest_date": str(m.get("created_at") or "")[:10],
            }
        sessions[key]["count"] += 1
        sessions[key]["total_obtained"] += int(m.get("obtained_marks") or 0)
        sessions[key]["total_possible"] += int(m.get("total_marks") or 0)
        ld = str(m.get("created_at") or "")[:10]
        if ld > sessions[key]["latest_date"]:
            sessions[key]["latest_date"] = ld

    session_list = []
    for s in sessions.values():
        s["avg_percent"] = round(s["total_obtained"] * 100 / s["total_possible"], 1) if s["total_possible"] else 0
        session_list.append(s)
    session_list.sort(key=lambda x: x["latest_date"], reverse=True)

    return render_template(
        "teacher/marks_history.html",
        sessions=session_list,
        classes=classes,
        subjects=subjects,
        class_filter=class_filter,
        subject_filter=subject_filter,
        exam_filter=exam_filter,
    )


@teacher_bp.route("/marks/view/<exam_type>/<int:class_id>/<int:subject_id>")
@role_required("teacher")
def marks_view(exam_type, class_id, subject_id):
    try:
        all_marks = table("marks").select("*").eq("subject_id", subject_id).eq("exam_type", exam_type).execute().data or []
    except Exception:
        all_marks = []

    profiles = _safe_select("students", class_id=class_id)
    student_ids = [p["user_id"] for p in profiles]
    marks_map = {m["student_user_id"]: m for m in all_marks if m["student_user_id"] in student_ids}

    users = _safe_select("users")
    umap = {u["id"]: u for u in users}

    rows = []
    for p in profiles:
        sid = p["user_id"]
        u = umap.get(sid, {})
        m = marks_map.get(sid)
        rows.append({
            "student_name": u.get("name", "-"),
            "roll_number": u.get("roll_number", "-"),
            "roll_no_in_class": p.get("roll_no_in_class", "-"),
            "obtained": m.get("obtained_marks") if m else None,
            "total": m.get("total_marks") if m else None,
            "percent": round(int(m["obtained_marks"]) * 100 / int(m["total_marks"]), 1) if m and m.get("total_marks") else 0,
        })
    rows.sort(key=lambda x: x["roll_no_in_class"] if isinstance(x["roll_no_in_class"], int) else 9999)

    cls = _get_one("classes", class_id)
    sub = _get_one("subjects", subject_id)

    with_marks = [r for r in rows if r["obtained"] is not None]
    avg = round(sum(r["percent"] for r in with_marks) / len(with_marks), 1) if with_marks else 0
    highest = max(with_marks, key=lambda x: x["percent"]) if with_marks else None
    lowest = min(with_marks, key=lambda x: x["percent"]) if with_marks else None

    return render_template(
        "teacher/marks_view.html",
        exam_type=exam_type,
        class_id=class_id,
        subject_id=subject_id,
        class_name=cls.get("name", "-"),
        subject_name=sub.get("name", "-"),
        rows=rows,
        stats={"count": len(with_marks), "avg": avg, "highest": highest, "lowest": lowest},
    )


@teacher_bp.route("/marks/edit/<exam_type>/<int:class_id>/<int:subject_id>", methods=["GET", "POST"])
@role_required("teacher")
def marks_edit(exam_type, class_id, subject_id):
    if request.method == "POST":
        saved = 0
        profiles = _safe_select("students", class_id=class_id)
        for p in profiles:
            sid = p["user_id"]
            obtained = request.form.get(f"marks_{sid}")
            total = request.form.get(f"total_{sid}")
            if obtained is None or obtained == "":
                continue
            try:
                obtained_int = int(obtained)
                total_int = int(total) if total and total.strip() else 100
            except ValueError:
                continue
            try:
                table("marks").delete().eq("student_user_id", sid).eq("subject_id", subject_id).eq("exam_type", exam_type).execute()
                table("marks").insert({
                    "student_user_id": sid,
                    "subject_id": subject_id,
                    "exam_type": exam_type,
                    "total_marks": total_int,
                    "obtained_marks": obtained_int,
                }).execute()
                saved += 1
            except Exception:
                pass
        flash(f"Marks updated for {saved}.", "success")
        return redirect(url_for("teacher.marks_view", exam_type=exam_type, class_id=class_id, subject_id=subject_id))

    profiles = _safe_select("students", class_id=class_id)
    student_ids = [p["user_id"] for p in profiles]
    try:
        existing = table("marks").select("*").eq("subject_id", subject_id).eq("exam_type", exam_type).execute().data or []
    except Exception:
        existing = []
    existing_map = {m["student_user_id"]: m for m in existing if m["student_user_id"] in student_ids}

    users = _safe_select("users")
    umap = {u["id"]: u for u in users}

    students_data = []
    for p in profiles:
        sid = p["user_id"]
        u = umap.get(sid, {})
        m = existing_map.get(sid, {})
        students_data.append({
            "user_id": sid,
            "name": u.get("name", "-"),
            "roll_number": u.get("roll_number", "-"),
            "roll_no_in_class": p.get("roll_no_in_class", "-"),
            "obtained": m.get("obtained_marks", ""),
            "total": m.get("total_marks", 100),
        })
    students_data.sort(key=lambda x: x["roll_no_in_class"] if isinstance(x["roll_no_in_class"], int) else 9999)

    cls = _get_one("classes", class_id)
    sub = _get_one("subjects", subject_id)

    return render_template(
        "teacher/marks_edit.html",
        exam_type=exam_type,
        class_id=class_id,
        subject_id=subject_id,
        class_name=cls.get("name", "-"),
        subject_name=sub.get("name", "-"),
        students=students_data,
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
    uid = session["user_id"]
    user_rows = _safe_select("users", id=uid)
    user = user_rows[0] if user_rows else {}
    teacher_rows = _safe_select("teachers", user_id=uid)
    teacher = teacher_rows[0] if teacher_rows else {}

    academy = {
        "name": "Academy Management System",
        "tagline": "Excellence in Education",
        "address": "123 Education Street, City",
        "phone": "+92 300 0000000",
        "website": "academy-ms.app",
        "session": "2025-2026",
    }

    return render_template("id_cards/teacher_card.html", user=user, teacher=teacher, academy=academy)

# =====================================================
# MY ATTENDANCE (Teacher sees own attendance)
# =====================================================
@teacher_bp.route("/my-attendance")
@role_required("teacher")
def my_attendance():
    """Teacher views own attendance history."""
    tid = session["user_id"]

    # Filter by month
    month = request.args.get("month") or date.today().strftime("%Y-%m")

    try:
        all_att = table("teacher_attendance").select("*").eq(
            "teacher_user_id", tid
        ).execute().data or []
    except Exception:
        all_att = []

    month_att = [a for a in all_att if str(a.get("date", "")).startswith(month)]
    month_att.sort(key=lambda x: x.get("date") or "", reverse=True)

    # Counts
    present = sum(1 for a in month_att if a["status"] == "P")
    absent = sum(1 for a in month_att if a["status"] == "A")
    late = sum(1 for a in month_att if a["status"] == "L")
    half_day = sum(1 for a in month_att if a["status"] == "H")
    leave = sum(1 for a in month_att if a["status"] == "LV")

    total = present + absent + late + half_day + leave
    att_percent = round((present + late) * 100 / total, 1) if total else 0

    # Salary info
    profile = _get_one("teachers", tid, field="user_id") if False else {}
    try:
        res = table("teachers").select("*").eq("user_id", tid).limit(1).execute()
        profile = res.data[0] if res.data else {}
    except Exception:
        profile = {}

    monthly_salary = float(profile.get("monthly_salary") or 0)

    # Deduction calculation
    FREE_LEAVES = 1
    FREE_LATES = 4
    LEAVE_DEDUCTION = 800
    LATE_DEDUCTION = 400

    extra_leaves = max(0, leave - FREE_LEAVES)
    extra_lates = max(0, late - FREE_LATES)

    leave_deduction = extra_leaves * LEAVE_DEDUCTION
    late_deduction = extra_lates * LATE_DEDUCTION
    total_deduction = leave_deduction + late_deduction
    net_salary = max(0, monthly_salary - total_deduction)

    return render_template(
        "teacher/my_attendance.html",
        month_att=month_att,
        month=month,
        counts={
            "present": present, "absent": absent, "late": late,
            "half_day": half_day, "leave": leave, "total": total,
        },
        att_percent=att_percent,
        salary={
            "monthly": monthly_salary,
            "extra_leaves": extra_leaves,
            "extra_lates": extra_lates,
            "leave_deduction": leave_deduction,
            "late_deduction": late_deduction,
            "total_deduction": total_deduction,
            "net_salary": net_salary,
        },
    )
# =====================================================
# HELPERS
# =====================================================
def _safe_select(table_name, **filters):
    try:
        q = table(table_name).select("*")
        for k, v in filters.items():
            q = q.eq(k, v)
        return q.execute().data or []
    except Exception as e:
        print(f"_safe_select error ({table_name}): {e}")
        return []


def _get_one(table_name, pk):
    try:
        res = table(table_name).select("*").eq("id", pk).limit(1).execute()
        return res.data[0] if res.data else {}
    except Exception:
        return {}


def _is_assigned(teacher_id, class_id, section_id, subject_id):
    try:
        res = table("teacher_assignments").select("id").eq("teacher_user_id", teacher_id).eq("class_id", class_id).eq("section_id", section_id).eq("subject_id", subject_id).limit(1).execute()
        return bool(res.data)
    except Exception:
        return False


def _students_in(class_id, section_id):
    try:
        profiles = table("students").select("*").eq("class_id", class_id).eq("section_id", section_id).execute().data or []
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
            out.append({
                "user_id": u["id"],
                "id": u["id"],
                "roll_number": u.get("roll_number"),
                "name": u.get("name"),
                "role": u.get("role"),
                "is_active": u.get("is_active"),
                "phone": u.get("phone"),
                "roll_no_in_class": p.get("roll_no_in_class"),
            })
        return sorted(out, key=lambda x: x.get("roll_no_in_class") or 9999)
    except Exception as e:
        print(f"_students_in error: {e}")
        return []


def _existing_attendance(date_str, class_id, section_id, subject_id):
    try:
        recs = table("attendance").select("*").eq("class_id", class_id).eq("section_id", section_id).eq("subject_id", subject_id).eq("date", date_str).execute().data or []
        return {r["student_user_id"]: r["status"] for r in recs}
    except Exception:
        return {}


def _recent_attendance(tid, limit=5):
    try:
        recs = table("attendance").select("*").eq("teacher_user_id", tid).order("date", desc=True).limit(500).execute().data or []
    except Exception:
        return []

    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")
    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}

    groups = {}
    for r in recs:
        key = (str(r.get("date")), r.get("class_id"), r.get("section_id"), r.get("subject_id"))
        if key not in groups:
            groups[key] = {
                "date": r.get("date"),
                "class_id": r.get("class_id"),
                "section_id": r.get("section_id"),
                "subject_id": r.get("subject_id"),
                "class_name": cmap.get(r.get("class_id"), "-"),
                "section_name": smap.get(r.get("section_id"), "-"),
                "subject_name": submap.get(r.get("subject_id"), "-"),
                "P": 0, "A": 0, "L": 0, "total": 0,
            }
        status = r.get("status")
        groups[key][status] = groups[key].get(status, 0) + 1
        groups[key]["total"] += 1

    sorted_list = sorted(groups.values(), key=lambda x: str(x["date"]), reverse=True)[:limit]
    for s in sorted_list:
        t = s["total"] or 1
        s["percent"] = round(s["P"] * 100 / t, 1)
    return sorted_list


def _recent_marks(tid, limit=5):
    try:
        assigns = _safe_select("teacher_assignments", teacher_user_id=tid)
        valid = {(a["class_id"], a["subject_id"]) for a in assigns}
        if not valid:
            return []
        all_marks = table("marks").select("*").order("created_at", desc=True).limit(300).execute().data or []
        profiles = _safe_select("students")
        pmap = {p["user_id"]: p for p in profiles}
        classes = _safe_select("classes")
        subjects = _safe_select("subjects")
        cmap = {c["id"]: c["name"] for c in classes}
        submap = {s["id"]: s["name"] for s in subjects}

        groups = {}
        for m in all_marks:
            sid = m.get("student_user_id")
            profile = pmap.get(sid)
            if not profile:
                continue
            cid = profile.get("class_id")
            sub_id = m.get("subject_id")
            if (cid, sub_id) not in valid:
                continue
            key = (m.get("exam_type"), cid, sub_id)
            if key not in groups:
                groups[key] = {
                    "exam_type": m.get("exam_type"),
                    "class_id": cid,
                    "class_name": cmap.get(cid, "-"),
                    "subject_id": sub_id,
                    "subject_name": submap.get(sub_id, "-"),
                    "count": 0,
                    "latest_date": str(m.get("created_at") or "")[:10],
                }
            groups[key]["count"] += 1

        return sorted(groups.values(), key=lambda x: x["latest_date"], reverse=True)[:limit]
    except Exception:
        return []
