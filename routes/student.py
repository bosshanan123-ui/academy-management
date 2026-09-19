"""
routes/student.py
Student dashboard, timetable, attendance, result, fee.
"""
from datetime import date

from flask import Blueprint, render_template, session

from utils.supabase_client import table
from utils.decorators import role_required

student_bp = Blueprint("student", __name__)


@student_bp.route("/dashboard")
@role_required("student")
def dashboard():
    uid = session["user_id"]
    profile = _profile(uid)
    ctx = _base_ctx(uid, profile)
    return render_template("student/dashboard.html", **ctx)


@student_bp.route("/timetable")
@role_required("student")
def timetable():
    uid = session["user_id"]
    profile = _profile(uid)
    ctx = _base_ctx(uid, profile)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    grid = {d: [e for e in ctx["all_tt"] if e["day"] == d] for d in days}
    return render_template("student/timetable.html", grid=grid, days=days, **ctx)


@student_bp.route("/attendance")
@role_required("student")
def attendance():
    """Attendance page: overall % + subject-wise + date-wise log."""
    uid = session["user_id"]
    profile = _profile(uid)
    ctx = _base_ctx(uid, profile)

    # Get all attendance records for this student
    all_att = _safe_select("attendance", student_user_id=uid)

    # Fetch subjects + teachers for name mapping
    subjects = _safe_select("subjects")
    submap = {s["id"]: s["name"] for s in subjects}
    users = _safe_select("users")
    umap = {u["id"]: u.get("name", "-") for u in users}

    # Subject-wise breakdown
    subject_stats = {}
    for a in all_att:
        sid = a.get("subject_id")
        if not sid:
            continue
        subject_stats.setdefault(sid, {
            "subject_name": submap.get(sid, "-"),
            "P": 0, "A": 0, "L": 0, "total": 0,
        })
        status = a.get("status", "P")
        subject_stats[sid][status] = subject_stats[sid].get(status, 0) + 1
        subject_stats[sid]["total"] += 1

    # Add percentage per subject
    subject_rows = []
    for sid, stats in subject_stats.items():
        total = stats["total"] or 1
        stats["percent"] = round(stats["P"] * 100 / total, 1)
        stats["subject_id"] = sid
        subject_rows.append(stats)
    subject_rows.sort(key=lambda x: x["subject_name"])

    # Date-wise log (recent first)
    log_rows = []
    for a in all_att:
        log_rows.append({
            "date": a.get("date"),
            "subject_name": submap.get(a.get("subject_id"), "-"),
            "teacher_name": umap.get(a.get("teacher_user_id"), "-"),
            "status": a.get("status", "-"),
        })
    log_rows.sort(key=lambda x: x["date"] or "", reverse=True)

    # Monthly calendar data (current month)
    from datetime import date as _date
    import calendar
    today = _date.today()
    year, month = today.year, today.month

    # Group by date for this month
    month_log = {}
    for a in all_att:
        d = a.get("date")
        if not d:
            continue
        try:
            y, m, day = str(d).split("-")
            if int(y) == year and int(m) == month:
                month_log[int(day)] = a.get("status", "-")
        except Exception:
            continue

    ctx.update({
        "subject_rows": subject_rows,
        "log_rows": log_rows,
        "month_log": month_log,
        "calendar_year": year,
        "calendar_month": month,
        "month_name": calendar.month_name[month],
        "days_in_month": calendar.monthrange(year, month)[1],
        "first_weekday": calendar.monthrange(year, month)[0],  # 0=Mon
    })

    return render_template("student/attendance.html", **ctx)


@student_bp.route("/result")
@role_required("student")
def result():
    uid = session["user_id"]
    profile = _profile(uid)
    ctx = _base_ctx(uid, profile)
    return render_template("student/result.html", **ctx)


@student_bp.route("/fee")
@role_required("student")
def fee():
    uid = session["user_id"]
    profile = _profile(uid)
    ctx = _base_ctx(uid, profile)
    return render_template("student/fee.html", **ctx)


# ---------- helpers ----------
def _profile(uid):
    try:
        res = table("students").select("*").eq("user_id", uid).limit(1).execute()
        return res.data[0] if res.data else {}
    except Exception:
        return {}


def _base_ctx(uid, profile):
    class_id = profile.get("class_id")
    section_id = profile.get("section_id")

    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")
    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}

    # Timetable for class+section
    all_tt = []
    today_tt = []
    today_name = date.today().strftime("%A")
    if class_id and section_id:
        try:
            res = table("timetable").select("*").eq(
                "class_id", class_id
            ).eq("section_id", section_id).execute()
            all_tt = res.data or []
        except Exception:
            all_tt = []

    users = _safe_select("users")
    umap = {u["id"]: u for u in users}

    for e in all_tt:
        e["class_name"] = cmap.get(e["class_id"], "-")
        e["section_name"] = smap.get(e["section_id"], "-")
        e["subject_name"] = submap.get(e["subject_id"], "-")
        e["teacher_name"] = umap.get(e["teacher_user_id"], {}).get("name", "-")
        if e["day"] == today_name:
            today_tt.append(e)

    # My teachers via assignments
    my_teachers = []
    if class_id and section_id:
        assigns = _safe_select("teacher_assignments",
                               class_id=class_id, section_id=section_id)
        for a in assigns:
            t = umap.get(a["teacher_user_id"], {})
            my_teachers.append({
                "subject": submap.get(a["subject_id"], "-"),
                "teacher_name": t.get("name", "-"),
                "teacher_roll": t.get("roll_number", "-"),
            })

    # Attendance summary
    att = _safe_select("attendance", student_user_id=uid)
    this_month = date.today().strftime("%Y-%m")
    monthly = [a for a in att if str(a.get("date", "")).startswith(this_month)]
    p = sum(1 for a in monthly if a["status"] == "P")
    ab = sum(1 for a in monthly if a["status"] == "A")
    lv = sum(1 for a in monthly if a["status"] == "L")
    total = p + ab + lv or 1
    att_percent = round(p * 100 / total, 1)

    # Marks
    marks = _safe_select("marks", student_user_id=uid)
    for m in marks:
        m["subject_name"] = submap.get(m["subject_id"], "-")

    # Fees
    fees = _safe_select("fees", student_user_id=uid)

    return {
        "profile": profile,
        "class_name": cmap.get(class_id, "-"),
        "section_name": smap.get(section_id, "-"),
        "today_tt": today_tt,
        "today_name": today_name,
        "my_teachers": my_teachers,
        "att_percent": att_percent,
        "att_counts": {"P": p, "A": ab, "L": lv},
        "marks": marks,
        "fees": fees,
        "all_tt": all_tt,
    }


def _safe_select(table_name, **filters):
    try:
        q = table(table_name).select("*")
        for k, v in filters.items():
            q = q.eq(k, v)
        return q.execute().data or []
    except Exception:
        return []
