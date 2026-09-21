"""
routes/principal.py
Principal: full read-only dashboard with reports.
"""
from datetime import date, timedelta
import calendar

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from utils.supabase_client import table
from utils.decorators import role_required

principal_bp = Blueprint("principal", __name__)


# =====================================================
# DASHBOARD
# =====================================================
@principal_bp.route("/dashboard")
@role_required("principal")
def dashboard():
    users = _safe_select("users")
    students = [u for u in users if u["role"] == "student"]
    teachers = [u for u in users if u["role"] == "teacher"]
    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")
    fees = _safe_select("fees")

    collected = sum(float(f.get("amount") or 0) for f in fees if f.get("status") == "paid")
    pending = sum(float(f.get("amount") or 0) for f in fees if f.get("status") != "paid")

    class_labels = [c["name"] for c in classes]
    students_p = _safe_select("students")
    class_counts = [sum(1 for s in students_p if s.get("class_id") == c["id"]) for c in classes]

    return render_template(
        "principal/dashboard.html",
        stats={
            "students": len(students),
            "teachers": len(teachers),
            "classes": len(classes),
            "sections": len(sections),
            "subjects": len(subjects),
            "collected": round(collected, 2),
            "pending": round(pending, 2),
        },
        class_labels=class_labels,
        class_counts=class_counts,
    )


# =====================================================
# ATTENDANCE REPORT
# =====================================================
@principal_bp.route("/attendance")
@role_required("principal")
def attendance():
    classes = _safe_select("classes")
    sections = _safe_select("sections")

    class_id = request.args.get("class_id", "").strip()
    section_id = request.args.get("section_id", "").strip()
    month = request.args.get("month", "").strip()

    if not month:
        month = date.today().strftime("%Y-%m")

    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}

    rows = []
    stats = {"present": 0, "absent": 0, "leave": 0, "total": 0, "percent": 0}

    if class_id and section_id:
        try:
            students = _safe_select("students", class_id=int(class_id), section_id=int(section_id))
            student_ids = [s["user_id"] for s in students]
            users = _safe_select("users")
            umap = {u["id"]: u for u in users}

            if student_ids:
                try:
                    all_att = table("attendance").select("*").in_("student_user_id", student_ids).execute().data or []
                except Exception:
                    all_att = []

                month_att = [a for a in all_att if str(a.get("date", "")).startswith(month)]

                for stu in students:
                    sid = stu["user_id"]
                    u = umap.get(sid, {})
                    stu_att = [a for a in month_att if a["student_user_id"] == sid]

                    p = sum(1 for a in stu_att if a["status"] == "P")
                    ab = sum(1 for a in stu_att if a["status"] == "A")
                    lv = sum(1 for a in stu_att if a["status"] == "L")
                    total = p + ab + lv or 1

                    rows.append({
                        "roll_no_in_class": stu.get("roll_no_in_class", "-"),
                        "roll_number": u.get("roll_number", "-"),
                        "name": u.get("name", "-"),
                        "present": p,
                        "absent": ab,
                        "leave": lv,
                        "total": p + ab + lv,
                        "percent": round(p * 100 / total, 1),
                    })

                rows.sort(key=lambda x: x["roll_no_in_class"] if isinstance(x["roll_no_in_class"], int) else 9999)

                stats["present"] = sum(r["present"] for r in rows)
                stats["absent"] = sum(r["absent"] for r in rows)
                stats["leave"] = sum(r["leave"] for r in rows)
                stats["total"] = stats["present"] + stats["absent"] + stats["leave"]
                stats["percent"] = round(stats["present"] * 100 / stats["total"], 1) if stats["total"] else 0
        except Exception as e:
            print(f"attendance error: {e}")

    return render_template(
        "principal/attendance.html",
        classes=classes,
        sections=sections,
        rows=rows,
        stats=stats,
        class_id=class_id,
        section_id=section_id,
        month=month,
        cmap=cmap,
        smap=smap,
    )


# =====================================================
# FEES REPORT
# =====================================================
@principal_bp.route("/fees")
@role_required("principal")
def fees():
    classes = _safe_select("classes")
    sections = _safe_select("sections")

    class_id = request.args.get("class_id", "").strip()
    section_id = request.args.get("section_id", "").strip()
    month = request.args.get("month", "").strip()

    if not month:
        month = date.today().strftime("%Y-%m")

    rows = []
    stats = {"paid": 0, "unpaid": 0, "total_amount": 0, "collected": 0}

    if class_id and section_id:
        try:
            students = _safe_select("students", class_id=int(class_id), section_id=int(section_id))
            student_ids = [s["user_id"] for s in students]
            users = _safe_select("users")
            umap = {u["id"]: u for u in users}

            if student_ids:
                try:
                    all_fees = table("fees").select("*").in_("student_user_id", student_ids).execute().data or []
                except Exception:
                    all_fees = []

                month_fees = [f for f in all_fees if f.get("month") == month]

                for stu in students:
                    sid = stu["user_id"]
                    u = umap.get(sid, {})
                    fee = next((f for f in month_fees if f["student_user_id"] == sid), None)

                    rows.append({
                        "roll_no_in_class": stu.get("roll_no_in_class", "-"),
                        "roll_number": u.get("roll_number", "-"),
                        "name": u.get("name", "-"),
                        "amount": float(fee["amount"]) if fee else 0,
                        "status": fee.get("status", "not_generated") if fee else "not_generated",
                        "paid_date": fee.get("paid_date", "-") if fee else "-",
                    })

                    if fee:
                        stats["total_amount"] += float(fee.get("amount") or 0)
                        if fee.get("status") == "paid":
                            stats["collected"] += float(fee.get("amount") or 0)
                            stats["paid"] += 1
                        else:
                            stats["unpaid"] += 1

            rows.sort(key=lambda x: x["roll_no_in_class"] if isinstance(x["roll_no_in_class"], int) else 9999)
        except Exception as e:
            print(f"fees error: {e}")

    return render_template(
        "principal/fees.html",
        classes=classes,
        sections=sections,
        rows=rows,
        stats=stats,
        class_id=class_id,
        section_id=section_id,
        month=month,
    )


# =====================================================
# MARKS REPORT
# =====================================================
@principal_bp.route("/marks")
@role_required("principal")
def marks():
    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")

    class_id = request.args.get("class_id", "").strip()
    section_id = request.args.get("section_id", "").strip()
    exam_type = request.args.get("exam_type", "").strip()

    submap = {s["id"]: s["name"] for s in subjects}

    rows = []
    stats = {"students": 0, "avg_percent": 0, "topper": None, "lowest": None}

    if class_id and section_id:
        try:
            students = _safe_select("students", class_id=int(class_id), section_id=int(section_id))
            student_ids = [s["user_id"] for s in students]
            users = _safe_select("users")
            umap = {u["id"]: u for u in users}

            if student_ids:
                try:
                    all_marks = table("marks").select("*").in_("student_user_id", student_ids).execute().data or []
                except Exception:
                    all_marks = []

                if exam_type:
                    all_marks = [m for m in all_marks if m.get("exam_type") == exam_type]

                for stu in students:
                    sid = stu["user_id"]
                    u = umap.get(sid, {})
                    stu_marks = [m for m in all_marks if m["student_user_id"] == sid]

                    total_obtained = sum(m.get("obtained_marks") or 0 for m in stu_marks)
                    total_possible = sum(m.get("total_marks") or 0 for m in stu_marks)
                    percent = round(total_obtained * 100 / total_possible, 1) if total_possible else 0

                    if percent >= 90: grade = "A+"
                    elif percent >= 80: grade = "A"
                    elif percent >= 70: grade = "B"
                    elif percent >= 60: grade = "C"
                    elif percent >= 50: grade = "D"
                    elif percent > 0: grade = "F"
                    else: grade = "-"

                    rows.append({
                        "roll_no_in_class": stu.get("roll_no_in_class", "-"),
                        "roll_number": u.get("roll_number", "-"),
                        "name": u.get("name", "-"),
                        "total_obtained": total_obtained,
                        "total_possible": total_possible,
                        "percent": percent,
                        "grade": grade,
                        "subjects_count": len(stu_marks),
                    })

                rows.sort(key=lambda x: x["percent"], reverse=True)

                with_marks = [r for r in rows if r["total_possible"] > 0]
                if with_marks:
                    stats["students"] = len(with_marks)
                    stats["avg_percent"] = round(sum(r["percent"] for r in with_marks) / len(with_marks), 1)
                    stats["topper"] = with_marks[0]
                    stats["lowest"] = with_marks[-1]
        except Exception as e:
            print(f"marks error: {e}")

    return render_template(
        "principal/marks.html",
        classes=classes,
        sections=sections,
        rows=rows,
        stats=stats,
        class_id=class_id,
        section_id=section_id,
        exam_type=exam_type,
    )


# =====================================================
# TEACHERS LIST
# =====================================================
@principal_bp.route("/teachers")
@role_required("principal")
def teachers():
    teachers_list = _safe_select("users", role="teacher")
    teacher_profiles = _safe_select("teachers")
    pmap = {t["user_id"]: t for t in teacher_profiles}

    teachers_data = []
    for t in teachers_list:
        p = pmap.get(t["id"], {})
        assigns = _safe_select("teacher_assignments", teacher_user_id=t["id"])
        teachers_data.append({
            "id": t["id"],
            "name": t.get("name", "-"),
            "roll_number": t.get("roll_number", "-"),
            "phone": t.get("phone", "-"),
            "email": t.get("email", "-"),
            "qualification": p.get("qualification", "-"),
            "assignments_count": len(assigns),
        })

    return render_template("principal/teachers.html", teachers=teachers_data)


@principal_bp.route("/teachers/<int:teacher_id>/timetable")
@role_required("principal")
def teacher_timetable(teacher_id):
    teacher_user = _get_one("users", teacher_id)
    teacher_profile = _get_one("teachers", teacher_id, field="user_id")

    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")
    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}

    entries = _safe_select("timetable", teacher_user_id=teacher_id)
    for e in entries:
        e["class_name"] = cmap.get(e["class_id"], "-")
        e["section_name"] = smap.get(e["section_id"], "-")
        e["subject_name"] = submap.get(e["subject_id"], "-")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    grid = {d: [e for e in entries if e["day"] == d] for d in days}

    return render_template(
        "principal/teacher_timetable.html",
        teacher=teacher_user,
        teacher_profile=teacher_profile,
        grid=grid,
        days=days,
        entries_count=len(entries),
    )


# =====================================================
# TIMETABLE
# =====================================================
@principal_bp.route("/timetable")
@role_required("principal")
def timetable():
    classes = _safe_select("classes")
    sections = _safe_select("sections")

    class_id = request.args.get("class_id", "").strip()
    section_id = request.args.get("section_id", "").strip()

    entries = []
    grid = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    if class_id and section_id:
        try:
            entries = table("timetable").select("*").eq(
                "class_id", int(class_id)
            ).eq("section_id", int(section_id)).execute().data or []
        except Exception:
            entries = []

        subjects = _safe_select("subjects")
        submap = {s["id"]: s["name"] for s in subjects}
        users = _safe_select("users")
        umap = {u["id"]: u for u in users}

        for e in entries:
            e["subject_name"] = submap.get(e["subject_id"], "-")
            e["teacher_name"] = umap.get(e["teacher_user_id"], {}).get("name", "-")

        grid = {d: [e for e in entries if e["day"] == d] for d in days}

    return render_template(
        "principal/timetable.html",
        classes=classes,
        sections=sections,
        grid=grid,
        days=days,
        class_id=class_id,
        section_id=section_id,
        has_data=bool(entries),
    )


# =====================================================
# NOTICES
# =====================================================
@principal_bp.route("/notices", methods=["GET", "POST"])
@role_required("principal")
def notices():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        target = request.form.get("target_role") or "all"
        if not title or not body:
            flash("Title and body are required.", "error")
        else:
            try:
                table("notices").insert({
                    "title": title,
                    "body": body,
                    "posted_by_user_id": session["user_id"],
                    "target_role": target,
                }).execute()
                flash("Notice posted.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
        return redirect(url_for("principal.notices"))

    try:
        rows = _safe_select("notices")
        users = _safe_select("users")
        umap = {u["id"]: u.get("name", "-") for u in users}

        reads = []
        try:
            res = table("notice_reads").select("*").execute()
            reads = res.data or []
        except Exception as e:
            print(f"notice_reads fetch error: {e}")
            reads = []

        total_users_by_role = {
            "all": sum(1 for u in users if u.get("role") in ("student", "parent", "teacher")),
            "student": sum(1 for u in users if u.get("role") == "student"),
            "parent": sum(1 for u in users if u.get("role") == "parent"),
            "teacher": sum(1 for u in users if u.get("role") == "teacher"),
        }

        for n in rows:
            n["posted_by"] = umap.get(n.get("posted_by_user_id"), "-")
            n["can_edit"] = (n.get("posted_by_user_id") == session.get("user_id"))
            try:
                n_reads = [r for r in reads if r.get("notice_id") == n.get("id")]
            except Exception:
                n_reads = []
            n["read_count"] = len(n_reads)
            target = n.get("target_role") or "all"
            n["total_target"] = total_users_by_role.get(target, 0)
            n["read_percent"] = round(n["read_count"] * 100 / n["total_target"], 1) if n["total_target"] else 0

        return render_template("principal/notices.html", notices=rows)

    except Exception as e:
        print(f"notices error: {e}")
        flash(f"Could not load notices: {e}", "error")
        return render_template("principal/notices.html", notices=[])


@principal_bp.route("/notices/edit/<int:nid>", methods=["POST"])
@role_required("principal")
def edit_notice(nid):
    try:
        existing = table("notices").select("*").eq("id", nid).limit(1).execute().data
        if not existing or existing[0]["posted_by_user_id"] != session["user_id"]:
            flash("You can only edit your own notices.", "error")
            return redirect(url_for("principal.notices"))

        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        target = request.form.get("target_role") or "all"
        if not title or not body:
            flash("Title and body are required.", "error")
        else:
            table("notices").update({"title": title, "body": body, "target_role": target}).eq("id", nid).execute()
            flash("Notice updated.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("principal.notices"))


@principal_bp.route("/notices/delete/<int:nid>", methods=["POST"])
@role_required("principal")
def delete_notice(nid):
    try:
        existing = table("notices").select("*").eq("id", nid).limit(1).execute().data
        if not existing or existing[0]["posted_by_user_id"] != session["user_id"]:
            flash("You can only delete your own notices.", "error")
            return redirect(url_for("principal.notices"))
        table("notices").delete().eq("id", nid).execute()
        flash("Notice deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("principal.notices"))


# =====================================================
# NOTICE READERS  ← YE ROUTE MISSING THA!
# =====================================================
@principal_bp.route("/notices/readers/<int:nid>")
@role_required("principal")
def notice_readers(nid):
    """View who read a notice."""
    notice = _get_one("notices", nid)
    readers = []
    try:
        reads = table("notice_reads").select("*").eq("notice_id", nid).execute().data or []
        user_ids = [r["user_id"] for r in reads]
        if user_ids:
            users = table("users").select("*").in_("id", user_ids).execute().data or []
            umap = {u["id"]: u for u in users}
            for r in reads:
                u = umap.get(r["user_id"], {})
                readers.append({
                    "name": u.get("name", "-"),
                    "roll_number": u.get("roll_number", "-"),
                    "role": u.get("role", "-"),
                    "read_at": r.get("read_at", "-"),
                })
    except Exception as e:
        print(f"readers error: {e}")

    return render_template("principal/notice_readers.html", notice=notice, readers=readers)


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


def _get_one(table_name, pk, field="id"):
    try:
        res = table(table_name).select("*").eq(field, pk).limit(1).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"_get_one error ({table_name}, {field}={pk}): {e}")
        return {}
