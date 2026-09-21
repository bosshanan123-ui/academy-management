"""
routes/parent.py
Parent views for their linked child's data + notices.
"""
from datetime import date

from flask import Blueprint, render_template, session

from utils.supabase_client import table
from utils.decorators import role_required

parent_bp = Blueprint("parent", __name__)


# =====================================================
# HELPER: Get linked child
# =====================================================
def _get_child(parent_uid):
    """Return (child_user, child_profile) or ({}, {})."""
    try:
        res = table("students").select("*").eq(
            "parent_user_id", parent_uid
        ).limit(1).execute()
        profile = res.data[0] if res.data else {}
        if not profile:
            return {}, {}
        u = table("users").select("*").eq("id", profile["user_id"]).limit(1).execute().data
        child = u[0] if u else {}
        return child, profile
    except Exception:
        return {}, {}


# =====================================================
# HELPER: Build context (child data + notices)
# =====================================================
def _build_ctx(parent_uid):
    """Build template context with child's data + notices."""
    child, profile = _get_child(parent_uid)
    if not child:
        return {"child": {}, "profile": {}, "has_child": False}

    class_id = profile.get("class_id")
    section_id = profile.get("section_id")

    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")
    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}

    users = _safe_select("users")
    umap = {u["id"]: u for u in users}

    # ---- Timetable ----
    all_tt = _safe_select("timetable", class_id=class_id, section_id=section_id) \
        if class_id and section_id else []
    today_name = date.today().strftime("%A")
    today_tt = []
    for e in all_tt:
        e["class_name"] = cmap.get(e["class_id"], "-")
        e["section_name"] = smap.get(e["section_id"], "-")
        e["subject_name"] = submap.get(e["subject_id"], "-")
        e["teacher_name"] = umap.get(e["teacher_user_id"], {}).get("name", "-")
        if e["day"] == today_name:
            today_tt.append(e)

    # ---- My Teachers ----
    my_teachers = []
    if class_id and section_id:
        assigns = _safe_select("teacher_assignments",
                               class_id=class_id, section_id=section_id)
        for a in assigns:
            t = umap.get(a["teacher_user_id"], {})
            my_teachers.append({
                "subject": submap.get(a["subject_id"], "-"),
                "teacher_name": t.get("name", "-"),
            })

    # ---- Attendance ----
    att = _safe_select("attendance", student_user_id=child["id"])
    this_month = date.today().strftime("%Y-%m")
    monthly = [a for a in att if str(a.get("date", "")).startswith(this_month)]
    p = sum(1 for a in monthly if a["status"] == "P")
    ab = sum(1 for a in monthly if a["status"] == "A")
    lv = sum(1 for a in monthly if a["status"] == "L")
    total = p + ab + lv or 1
    att_percent = round(p * 100 / total, 1)

    # ---- Marks ----
    marks = _safe_select("marks", student_user_id=child["id"])
    for m in marks:
        m["subject_name"] = submap.get(m["subject_id"], "-")

    # ---- Fees ----
    fees = _safe_select("fees", student_user_id=child["id"])

    # ---- Notices ---- (NEW)
    notices = []
    try:
        raw_notices = table("notices").select("*").order(
            "created_at", desc=True
        ).limit(10).execute().data or []
        for n in raw_notices:
            target = n.get("target_role") or "all"
            # Show only notices for parents / all
            if target in ("all", "parent"):
                n["posted_by"] = umap.get(n.get("posted_by_user_id"), {}).get("name", "Admin")
                notices.append(n)
    except Exception as e:
        print(f"notices error: {e}")
        notices = []

    return {
        "has_child": True,
        "child": child,
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
        "notices": notices,   # ← NEW
    }


# =====================================================
# DASHBOARD
# =====================================================
@parent_bp.route("/dashboard")
@role_required("parent")
def dashboard():
    ctx = _build_ctx(session["user_id"])
    return render_template("parent/dashboard.html", **ctx)


# =====================================================
# ATTENDANCE
# =====================================================
@parent_bp.route("/attendance")
@role_required("parent")
def attendance():
    ctx = _build_ctx(session["user_id"])
    return render_template("parent/attendance.html", **ctx)


# =====================================================
# RESULT
# =====================================================
@parent_bp.route("/result")
@role_required("parent")
def result():
    ctx = _build_ctx(session["user_id"])
    return render_template("parent/result.html", **ctx)


# =====================================================
# FEES
# =====================================================
@parent_bp.route("/fee")
@role_required("parent")
def fee():
    ctx = _build_ctx(session["user_id"])
    return render_template("parent/fee.html", **ctx)


# =====================================================
# HELPER: Safe select
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
