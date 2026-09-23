"""
routes/super_admin.py
All Super Admin functionality with teacher salary support.
"""
from datetime import date

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)

from utils.supabase_client import table
from utils.decorators import role_required
from utils.roll_number import generate_roll_number
from utils.password_utils import hash_password

super_admin_bp = Blueprint("super_admin", __name__)


# =====================================================
# DASHBOARD
# =====================================================
@super_admin_bp.route("/dashboard")
@role_required("super_admin")
def dashboard():
    students = _safe_select("users", role="student")
    teachers = _safe_select("users", role="teacher")
    parents = _safe_select("users", role="parent")
    classes = _safe_select("classes")
    fees = _safe_select("fees")

    total_collected = sum(float(f.get("amount") or 0) for f in fees if f.get("status") == "paid")
    total_pending = sum(float(f.get("amount") or 0) for f in fees if f.get("status") != "paid")

    student_profiles = _safe_select("students")
    class_labels = []
    class_counts = []
    for c in classes:
        class_labels.append(c["name"])
        class_counts.append(sum(1 for s in student_profiles if s.get("class_id") == c["id"]))

    month_totals = {}
    for f in fees:
        if f.get("status") == "paid":
            m = f.get("month") or "Unknown"
            month_totals[m] = month_totals.get(m, 0) + float(f.get("amount") or 0)
    fee_labels = list(month_totals.keys())
    fee_values = list(month_totals.values())

    attendance = _safe_select("attendance")
    trend = {}
    for a in attendance:
        d = a.get("date")
        if not d:
            continue
        trend.setdefault(d, {"P": 0, "A": 0, "L": 0})
        trend[d][a.get("status", "P")] = trend[d].get(a.get("status", "P"), 0) + 1
    sorted_dates = sorted(trend.keys())[-30:]
    att_present = [trend[d]["P"] for d in sorted_dates]
    att_absent = [trend[d]["A"] for d in sorted_dates]

    return render_template(
        "super_admin/dashboard.html",
        stats={
            "students": len(students),
            "teachers": len(teachers),
            "parents": len(parents),
            "classes": len(classes),
            "collected": round(total_collected, 2),
            "pending": round(total_pending, 2),
        },
        class_labels=class_labels,
        class_counts=class_counts,
        fee_labels=fee_labels,
        fee_values=fee_values,
        att_dates=sorted_dates,
        att_present=att_present,
        att_absent=att_absent,
    )


# =====================================================
# CLASSES
# =====================================================
@super_admin_bp.route("/classes", methods=["GET", "POST"])
@role_required("super_admin")
def classes():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Class name is required.", "error")
        else:
            try:
                table("classes").insert({"name": name}).execute()
                flash(f"Class '{name}' created.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
        return redirect(url_for("super_admin.classes"))

    rows = _safe_select("classes")
    return render_template("super_admin/classes.html", classes=rows)


@super_admin_bp.route("/classes/delete/<int:cid>", methods=["POST"])
@role_required("super_admin")
def delete_class(cid):
    try:
        table("classes").delete().eq("id", cid).execute()
        flash("Class deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.classes"))


@super_admin_bp.route("/classes/edit/<int:cid>", methods=["POST"])
@role_required("super_admin")
def edit_class(cid):
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Class name is required.", "error")
    else:
        try:
            table("classes").update({"name": name}).eq("id", cid).execute()
            flash("Class updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.classes"))


# =====================================================
# SECTIONS
# =====================================================
@super_admin_bp.route("/sections", methods=["GET", "POST"])
@role_required("super_admin")
def sections():
    if request.method == "POST":
        class_id = request.form.get("class_id")
        name = (request.form.get("name") or "").strip().upper()
        if not class_id or not name:
            flash("Class and section name are required.", "error")
        else:
            try:
                table("sections").insert({"class_id": int(class_id), "name": name}).execute()
                flash("Section created.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
        return redirect(url_for("super_admin.sections"))

    secs = _safe_select("sections")
    cls = _safe_select("classes")
    class_map = {c["id"]: c["name"] for c in cls}
    for s in secs:
        s["class_name"] = class_map.get(s["class_id"], "?")
    return render_template("super_admin/sections.html", sections=secs, classes=cls)


@super_admin_bp.route("/sections/edit/<int:sid>", methods=["POST"])
@role_required("super_admin")
def edit_section(sid):
    class_id = request.form.get("class_id")
    name = (request.form.get("name") or "").strip().upper()
    if not class_id or not name:
        flash("Required fields missing.", "error")
    else:
        try:
            table("sections").update({"class_id": int(class_id), "name": name}).eq("id", sid).execute()
            flash("Section updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.sections"))


@super_admin_bp.route("/sections/delete/<int:sid>", methods=["POST"])
@role_required("super_admin")
def delete_section(sid):
    try:
        table("sections").delete().eq("id", sid).execute()
        flash("Section deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.sections"))


# =====================================================
# SUBJECTS
# =====================================================
@super_admin_bp.route("/subjects", methods=["GET", "POST"])
@role_required("super_admin")
def subjects():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        code = (request.form.get("code") or "").strip().upper()
        if not name:
            flash("Subject name is required.", "error")
        else:
            try:
                table("subjects").insert({"name": name, "code": code}).execute()
                flash("Subject created.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
        return redirect(url_for("super_admin.subjects"))

    return render_template("super_admin/subjects.html", subjects=_safe_select("subjects"))


@super_admin_bp.route("/subjects/edit/<int:sid>", methods=["POST"])
@role_required("super_admin")
def edit_subject(sid):
    name = (request.form.get("name") or "").strip()
    code = (request.form.get("code") or "").strip().upper()
    if not name:
        flash("Subject name is required.", "error")
    else:
        try:
            table("subjects").update({"name": name, "code": code}).eq("id", sid).execute()
            flash("Subject updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.subjects"))


@super_admin_bp.route("/subjects/delete/<int:sid>", methods=["POST"])
@role_required("super_admin")
def delete_subject(sid):
    try:
        table("subjects").delete().eq("id", sid).execute()
        flash("Subject deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.subjects"))


# =====================================================
# TEACHERS
# =====================================================
@super_admin_bp.route("/teachers", methods=["GET", "POST"])
@role_required("super_admin")
def teachers():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""
        qualification = (request.form.get("qualification") or "").strip()
        email = (request.form.get("email") or "").strip()
        monthly_salary = request.form.get("monthly_salary") or 0
        designation = (request.form.get("designation") or "").strip()
        cnic = (request.form.get("cnic") or "").strip()
        address = (request.form.get("address") or "").strip()

        if not name or not password:
            flash("Name and password are required.", "error")
            return redirect(url_for("super_admin.teachers"))

        try:
            roll = generate_roll_number("teacher")
            user = table("users").insert({
                "roll_number": roll,
                "password_hash": hash_password(password),
                "role": "teacher",
                "name": name,
                "phone": phone,
                "email": email,
            }).execute().data[0]

            # Build teacher profile payload
            teacher_payload = {
                "user_id": user["id"],
                "qualification": qualification,
                "joining_date": str(date.today()),
                "designation": designation,
                "cnic": cnic,
                "address": address,
            }
            try:
                teacher_payload["monthly_salary"] = float(monthly_salary) if monthly_salary else 0
            except (ValueError, TypeError):
                teacher_payload["monthly_salary"] = 0

            table("teachers").insert(teacher_payload).execute()

            flash(f"Teacher created. Roll Number: {roll}", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("super_admin.teachers"))

    teacher_users = _safe_select("users", role="teacher")
    tprofiles = _safe_select("teachers")
    pmap = {t["user_id"]: t for t in tprofiles}
    for u in teacher_users:
        u["profile"] = pmap.get(u["id"], {})
    return render_template("super_admin/teachers.html", teachers=teacher_users)


@super_admin_bp.route("/teachers/edit/<int:uid>", methods=["POST"])
@role_required("super_admin")
def edit_teacher(uid):
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    qualification = (request.form.get("qualification") or "").strip()
    designation = (request.form.get("designation") or "").strip()
    cnic = (request.form.get("cnic") or "").strip()
    address = (request.form.get("address") or "").strip()
    monthly_salary = request.form.get("monthly_salary") or 0

    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("super_admin.teachers"))

    try:
        table("users").update({"name": name, "phone": phone, "email": email}).eq("id", uid).execute()

        payload = {
            "qualification": qualification,
            "designation": designation,
            "cnic": cnic,
            "address": address,
        }
        try:
            payload["monthly_salary"] = float(monthly_salary) if monthly_salary else 0
        except (ValueError, TypeError):
            payload["monthly_salary"] = 0

        existing = table("teachers").select("id").eq("user_id", uid).execute().data
        if existing:
            table("teachers").update(payload).eq("user_id", uid).execute()
        else:
            payload["user_id"] = uid
            payload["joining_date"] = str(date.today())
            table("teachers").insert(payload).execute()

        flash("Teacher updated.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.teachers"))


@super_admin_bp.route("/teachers/reset-password/<int:uid>", methods=["POST"])
@role_required("super_admin")
def reset_teacher_password(uid):
    new_password = request.form.get("new_password") or ""
    if len(new_password) < 4:
        flash("Password must be at least 4 characters.", "error")
    else:
        try:
            table("users").update({"password_hash": hash_password(new_password)}).eq("id", uid).execute()
            flash("Password reset successfully.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.teachers"))


@super_admin_bp.route("/teachers/delete/<int:uid>", methods=["POST"])
@role_required("super_admin")
def delete_teacher(uid):
    try:
        table("users").delete().eq("id", uid).execute()
        flash("Teacher deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.teachers"))


# =====================================================
# STUDENTS
# =====================================================
@super_admin_bp.route("/students", methods=["GET", "POST"])
@role_required("super_admin")
def students():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        password = request.form.get("password") or ""
        phone = (request.form.get("phone") or "").strip()
        class_id = request.form.get("class_id")
        section_id = request.form.get("section_id")
        guardian_name = (request.form.get("guardian_name") or "").strip()
        guardian_phone = (request.form.get("guardian_phone") or "").strip()
        address = (request.form.get("address") or "").strip()
        roll_in_class = request.form.get("roll_no_in_class") or 0
        parent_user_id = request.form.get("parent_user_id")
        custom_fee_raw = request.form.get("custom_fee") or ""

        if not name or not password or not class_id or not section_id:
            flash("Name, password, class and section are required.", "error")
            return redirect(url_for("super_admin.students"))

        custom_fee = None
        if custom_fee_raw.strip():
            try:
                custom_fee = float(custom_fee_raw)
            except ValueError:
                custom_fee = None

        try:
            roll = generate_roll_number("student")
            user = table("users").insert({
                "roll_number": roll,
                "password_hash": hash_password(password),
                "role": "student",
                "name": name,
                "phone": phone,
            }).execute().data[0]

            student_payload = {
                "user_id": user["id"],
                "class_id": int(class_id),
                "section_id": int(section_id),
                "roll_no_in_class": int(roll_in_class) if str(roll_in_class).isdigit() else 0,
                "guardian_name": guardian_name,
                "guardian_phone": guardian_phone,
                "address": address,
            }
            if parent_user_id:
                student_payload["parent_user_id"] = int(parent_user_id)
            if custom_fee is not None:
                student_payload["custom_fee"] = custom_fee
            table("students").insert(student_payload).execute()

            flash(f"Student created. Roll Number: {roll}", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("super_admin.students"))

    cls = _safe_select("classes")
    secs = _safe_select("sections")
    parents = _safe_select("users", role="parent")
    student_users = _safe_select("users", role="student")
    student_profiles = _safe_select("students")

    profile_map = {s["user_id"]: s for s in student_profiles}
    class_map = {c["id"]: c["name"] for c in cls}
    section_map = {s["id"]: s["name"] for s in secs}
    parent_map = {p["id"]: p["roll_number"] for p in parents}

    for u in student_users:
        p = profile_map.get(u["id"], {})
        u["class_id"] = p.get("class_id")
        u["section_id"] = p.get("section_id")
        u["class_name"] = class_map.get(p.get("class_id"), "-")
        u["section_name"] = section_map.get(p.get("section_id"), "-")
        u["parent_roll"] = parent_map.get(p.get("parent_user_id"), "-")
        u["parent_user_id"] = p.get("parent_user_id")
        u["roll_no_in_class"] = p.get("roll_no_in_class", "-")
        u["custom_fee"] = p.get("custom_fee")
        u["guardian_name"] = p.get("guardian_name", "")
        u["guardian_phone"] = p.get("guardian_phone", "")
        u["address"] = p.get("address", "")

    return render_template("super_admin/students.html", students=student_users, classes=cls, sections=secs, parents=parents)


@super_admin_bp.route("/students/edit/<int:uid>", methods=["POST"])
@role_required("super_admin")
def edit_student(uid):
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    class_id = request.form.get("class_id")
    section_id = request.form.get("section_id")
    guardian_name = (request.form.get("guardian_name") or "").strip()
    guardian_phone = (request.form.get("guardian_phone") or "").strip()
    address = (request.form.get("address") or "").strip()
    roll_in_class = request.form.get("roll_no_in_class") or 0
    parent_user_id = request.form.get("parent_user_id")
    custom_fee_raw = request.form.get("custom_fee") or ""

    if not name or not class_id or not section_id:
        flash("Name, class and section are required.", "error")
        return redirect(url_for("super_admin.students"))

    custom_fee = None
    if custom_fee_raw.strip():
        try:
            custom_fee = float(custom_fee_raw)
        except ValueError:
            custom_fee = None

    try:
        table("users").update({"name": name, "phone": phone}).eq("id", uid).execute()
        payload = {
            "class_id": int(class_id),
            "section_id": int(section_id),
            "roll_no_in_class": int(roll_in_class) if str(roll_in_class).isdigit() else 0,
            "guardian_name": guardian_name,
            "guardian_phone": guardian_phone,
            "address": address,
            "custom_fee": custom_fee,
        }
        if parent_user_id:
            payload["parent_user_id"] = int(parent_user_id)
        else:
            payload["parent_user_id"] = None
        table("students").update(payload).eq("user_id", uid).execute()
        flash("Student updated.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.students"))


@super_admin_bp.route("/students/reset-password/<int:uid>", methods=["POST"])
@role_required("super_admin")
def reset_student_password(uid):
    new_password = request.form.get("new_password") or ""
    if len(new_password) < 4:
        flash("Password must be at least 4 characters.", "error")
    else:
        try:
            table("users").update({"password_hash": hash_password(new_password)}).eq("id", uid).execute()
            flash("Password reset successfully.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.students"))


@super_admin_bp.route("/students/delete/<int:uid>", methods=["POST"])
@role_required("super_admin")
def delete_student(uid):
    try:
        table("users").delete().eq("id", uid).execute()
        flash("Student deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.students"))


# =====================================================
# PARENTS
# =====================================================
@super_admin_bp.route("/parents", methods=["GET", "POST"])
@role_required("super_admin")
def parents():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        password = request.form.get("password") or ""
        phone = (request.form.get("phone") or "").strip()
        student_user_id = request.form.get("student_user_id")

        if not name or not password:
            flash("Name and password are required.", "error")
            return redirect(url_for("super_admin.parents"))

        try:
            roll = generate_roll_number("parent")
            user = table("users").insert({
                "roll_number": roll,
                "password_hash": hash_password(password),
                "role": "parent",
                "name": name,
                "phone": phone,
            }).execute().data[0]

            if student_user_id:
                table("students").update({"parent_user_id": user["id"]}).eq("user_id", int(student_user_id)).execute()

            flash(f"Parent created. Roll Number: {roll}", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("super_admin.parents"))

    parents_list = _safe_select("users", role="parent")
    students_list = _safe_select("users", role="student")
    student_profiles = _safe_select("students")

    for p in parents_list:
        linked = next((s for s in student_profiles if s.get("parent_user_id") == p["id"]), None)
        if linked:
            su = next((u for u in students_list if u["id"] == linked["user_id"]), None)
            p["linked_student"] = su["name"] if su else "-"
            p["linked_roll"] = su["roll_number"] if su else "-"
            p["linked_student_user_id"] = linked["user_id"]
        else:
            p["linked_student"] = "-"
            p["linked_roll"] = "-"
            p["linked_student_user_id"] = None

    return render_template("super_admin/parents.html", parents=parents_list, students=students_list)


@super_admin_bp.route("/parents/edit/<int:uid>", methods=["POST"])
@role_required("super_admin")
def edit_parent(uid):
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    student_user_id = request.form.get("student_user_id")

    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("super_admin.parents"))

    try:
        table("users").update({"name": name, "phone": phone}).eq("id", uid).execute()
        all_profiles = _safe_select("students")
        for sp in all_profiles:
            if sp.get("parent_user_id") == uid:
                table("students").update({"parent_user_id": None}).eq("id", sp["id"]).execute()
        if student_user_id:
            table("students").update({"parent_user_id": uid}).eq("user_id", int(student_user_id)).execute()
        flash("Parent updated.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.parents"))


@super_admin_bp.route("/parents/reset-password/<int:uid>", methods=["POST"])
@role_required("super_admin")
def reset_parent_password(uid):
    new_password = request.form.get("new_password") or ""
    if len(new_password) < 4:
        flash("Password must be at least 4 characters.", "error")
    else:
        try:
            table("users").update({"password_hash": hash_password(new_password)}).eq("id", uid).execute()
            flash("Password reset successfully.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.parents"))


@super_admin_bp.route("/parents/delete/<int:uid>", methods=["POST"])
@role_required("super_admin")
def delete_parent(uid):
    try:
        table("users").delete().eq("id", uid).execute()
        flash("Parent deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.parents"))


# =====================================================
# ASSIGNMENTS
# =====================================================
@super_admin_bp.route("/assignments", methods=["GET", "POST"])
@role_required("super_admin")
def assignments():
    if request.method == "POST":
        teacher_user_id = request.form.get("teacher_user_id")
        class_id = request.form.get("class_id")
        section_id = request.form.get("section_id")
        subject_id = request.form.get("subject_id")

        if not all([teacher_user_id, class_id, section_id, subject_id]):
            flash("All fields are required.", "error")
        else:
            try:
                table("teacher_assignments").insert({
                    "teacher_user_id": int(teacher_user_id),
                    "class_id": int(class_id),
                    "section_id": int(section_id),
                    "subject_id": int(subject_id),
                }).execute()
                flash("Assignment created.", "success")
            except Exception as e:
                flash(f"Error (possibly duplicate): {e}", "error")
        return redirect(url_for("super_admin.assignments"))

    assigns = _safe_select("teacher_assignments")
    teachers = _safe_select("users", role="teacher")
    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")

    tmap = {t["id"]: t for t in teachers}
    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}

    for a in assigns:
        t = tmap.get(a["teacher_user_id"], {})
        a["teacher_name"] = t.get("name", "-")
        a["teacher_roll"] = t.get("roll_number", "-")
        a["class_name"] = cmap.get(a["class_id"], "-")
        sec = smap.get(a["section_id"], {})
        a["section_name"] = sec.get("name", "-")
        a["subject_name"] = submap.get(a["subject_id"], "-")

    return render_template("super_admin/assignments.html", assignments=assigns, teachers=teachers, classes=classes, sections=sections, subjects=subjects)


@super_admin_bp.route("/assignments/delete/<int:aid>", methods=["POST"])
@role_required("super_admin")
def delete_assignment(aid):
    try:
        table("teacher_assignments").delete().eq("id", aid).execute()
        flash("Assignment deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.assignments"))


# =====================================================
# TIMETABLE
# =====================================================
@super_admin_bp.route("/timetable", methods=["GET", "POST"])
@role_required("super_admin")
def timetable():
    if request.method == "POST":
        payload = {
            "class_id": int(request.form.get("class_id")),
            "section_id": int(request.form.get("section_id")),
            "subject_id": int(request.form.get("subject_id")),
            "teacher_user_id": int(request.form.get("teacher_user_id")),
            "day": request.form.get("day"),
            "period_no": int(request.form.get("period_no") or 1),
            "start_time": request.form.get("start_time"),
            "end_time": request.form.get("end_time"),
        }
        try:
            table("timetable").insert(payload).execute()
            flash("Timetable entry added.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("super_admin.timetable"))

    filter_class = (request.args.get("class_id") or "").strip()
    filter_teacher = (request.args.get("teacher_user_id") or "").strip()
    filter_day = (request.args.get("day") or "").strip()

    entries = _safe_select("timetable")
    classes = _safe_select("classes")
    sections = _safe_select("sections")
    subjects = _safe_select("subjects")
    teachers = _safe_select("users", role="teacher")

    cmap = {c["id"]: c["name"] for c in classes}
    smap = {s["id"]: s["name"] for s in sections}
    submap = {s["id"]: s["name"] for s in subjects}
    tmap = {t["id"]: t for t in teachers}

    if filter_class:
        entries = [e for e in entries if str(e.get("class_id")) == filter_class]
    if filter_teacher:
        entries = [e for e in entries if str(e.get("teacher_user_id")) == filter_teacher]
    if filter_day:
        entries = [e for e in entries if e.get("day") == filter_day]

    for e in entries:
        e["class_name"] = cmap.get(e["class_id"], "-")
        e["section_name"] = smap.get(e["section_id"], "-")
        e["subject_name"] = submap.get(e["subject_id"], "-")
        e["teacher_name"] = tmap.get(e["teacher_user_id"], {}).get("name", "-")

    grid = {}
    for e in entries:
        key = f"{e['class_name']}-{e['section_name']}"
        grid.setdefault(key, []).append(e)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    return render_template(
        "super_admin/timetable.html",
        entries=entries,
        grid=grid,
        classes=classes,
        sections=sections,
        subjects=subjects,
        teachers=teachers,
        days=days,
        filter_class=filter_class,
        filter_teacher=filter_teacher,
        filter_day=filter_day,
    )


@super_admin_bp.route("/timetable/edit/<int:tid>", methods=["POST"])
@role_required("super_admin")
def edit_timetable(tid):
    try:
        payload = {
            "class_id": int(request.form.get("class_id")),
            "section_id": int(request.form.get("section_id")),
            "subject_id": int(request.form.get("subject_id")),
            "teacher_user_id": int(request.form.get("teacher_user_id")),
            "day": request.form.get("day"),
            "period_no": int(request.form.get("period_no") or 1),
            "start_time": request.form.get("start_time"),
            "end_time": request.form.get("end_time"),
        }
        table("timetable").update(payload).eq("id", tid).execute()
        flash("Timetable entry updated.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.timetable"))


@super_admin_bp.route("/timetable/delete/<int:tid>", methods=["POST"])
@role_required("super_admin")
def delete_timetable(tid):
    try:
        table("timetable").delete().eq("id", tid).execute()
        flash("Entry deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.timetable"))


# =====================================================
# FEES
# =====================================================
@super_admin_bp.route("/fees", methods=["GET", "POST"])
@role_required("super_admin")
def fees():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "save_structure":
            class_id = request.form.get("class_id")
            monthly_fee = request.form.get("monthly_fee") or 0
            admission_fee = request.form.get("admission_fee") or 0
            exam_fee = request.form.get("exam_fee") or 0
            notes = (request.form.get("notes") or "").strip()
            if not class_id:
                flash("Class is required.", "error")
                return redirect(url_for("super_admin.fees"))
            try:
                payload = {"class_id": int(class_id), "monthly_fee": float(monthly_fee), "admission_fee": float(admission_fee), "exam_fee": float(exam_fee), "notes": notes}
                existing = table("fee_structures").select("id").eq("class_id", int(class_id)).execute().data
                if existing:
                    table("fee_structures").update(payload).eq("class_id", int(class_id)).execute()
                    flash("Fee structure updated.", "success")
                else:
                    table("fee_structures").insert(payload).execute()
                    flash("Fee structure created.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
            return redirect(url_for("super_admin.fees"))

        if action == "generate":
            month = (request.form.get("month") or "").strip()
            mode = request.form.get("mode") or "all"
            target_class_id = request.form.get("target_class_id")
            target_student_id = request.form.get("target_student_id")
            override_amount = request.form.get("override_amount") or ""
            if not month:
                flash("Month is required.", "error")
                return redirect(url_for("super_admin.fees"))

            structures = _safe_select("fee_structures")
            struct_map = {s["class_id"]: s for s in structures}
            student_users = _safe_select("users", role="student")
            student_profiles = _safe_select("students")
            profile_map = {p["user_id"]: p for p in student_profiles}
            existing = _safe_select("fees")
            existing_set = {(f["student_user_id"], f["month"]) for f in existing}

            count, skipped, failed = 0, 0, []
            for u in student_users:
                sid = u["id"]
                if mode == "student" and str(sid) != str(target_student_id):
                    continue
                profile = profile_map.get(sid)
                if not profile:
                    continue
                if mode == "class" and str(profile.get("class_id")) != str(target_class_id):
                    continue
                if (sid, month) in existing_set:
                    skipped += 1
                    continue
                amount = 0
                if override_amount and str(override_amount).strip():
                    try:
                        amount = float(override_amount)
                    except ValueError:
                        pass
                elif profile.get("custom_fee"):
                    amount = float(profile["custom_fee"])
                else:
                    s = struct_map.get(profile.get("class_id"))
                    if s:
                        amount = float(s.get("monthly_fee") or 0)
                if amount <= 0:
                    failed.append(u.get("name", "?"))
                    continue
                try:
                    table("fees").insert({"student_user_id": sid, "month": month, "amount": amount, "status": "unpaid"}).execute()
                    count += 1
                except Exception as e:
                    failed.append(f"{u.get('name')} ({e})")

            msg = f"{count} voucher(s) generated for {month}."
            if skipped:
                msg += f" {skipped} existed."
            flash(msg, "success")
            return redirect(url_for("super_admin.fees"))

        if action == "delete_structure":
            sid = request.form.get("structure_id")
            try:
                table("fee_structures").delete().eq("id", int(sid)).execute()
                flash("Deleted.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
            return redirect(url_for("super_admin.fees"))

        if action == "mark_paid":
            fid = request.form.get("fee_id")
            try:
                table("fees").update({"status": "paid", "paid_date": str(date.today())}).eq("id", int(fid)).execute()
                flash("Marked paid.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
            return redirect(url_for("super_admin.fees"))

        if action == "mark_unpaid":
            fid = request.form.get("fee_id")
            try:
                table("fees").update({"status": "unpaid", "paid_date": None}).eq("id", int(fid)).execute()
                flash("Marked unpaid.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
            return redirect(url_for("super_admin.fees"))

        if action == "delete_voucher":
            fid = request.form.get("fee_id")
            try:
                table("fees").delete().eq("id", int(fid)).execute()
                flash("Voucher deleted.", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
            return redirect(url_for("super_admin.fees"))

        if action == "bulk_paid":
            ids = request.form.getlist("fee_ids")
            count = 0
            for fid in ids:
                try:
                    table("fees").update({"status": "paid", "paid_date": str(date.today())}).eq("id", int(fid)).execute()
                    count += 1
                except Exception:
                    pass
            flash(f"{count} marked paid.", "success")
            return redirect(url_for("super_admin.fees"))

        if action == "bulk_unpaid":
            ids = request.form.getlist("fee_ids")
            count = 0
            for fid in ids:
                try:
                    table("fees").update({"status": "unpaid", "paid_date": None}).eq("id", int(fid)).execute()
                    count += 1
                except Exception:
                    pass
            flash(f"{count} marked unpaid.", "success")
            return redirect(url_for("super_admin.fees"))

        if action == "bulk_delete":
            ids = request.form.getlist("fee_ids")
            count = 0
            for fid in ids:
                try:
                    table("fees").delete().eq("id", int(fid)).execute()
                    count += 1
                except Exception:
                    pass
            flash(f"{count} deleted.", "success")
            return redirect(url_for("super_admin.fees"))

        return redirect(url_for("super_admin.fees"))

    fees_list = _safe_select("fees")
    students = _safe_select("users", role="student")
    student_profiles = _safe_select("students")
    classes = _safe_select("classes")
    structures = _safe_select("fee_structures")

    smap = {s["id"]: s for s in students}
    cmap = {c["id"]: c for c in classes}
    pmap = {p["user_id"]: p for p in student_profiles}

    for f in fees_list:
        stu = smap.get(f["student_user_id"], {})
        profile = pmap.get(f["student_user_id"], {})
        f["student_name"] = stu.get("name", "-")
        f["student_roll"] = stu.get("roll_number", "-")
        cls = cmap.get(profile.get("class_id"), {})
        f["class_name"] = cls.get("name", "-")

    for s in structures:
        cls = cmap.get(s["class_id"], {})
        s["class_name"] = cls.get("name", "-")

    for u in students:
        profile = pmap.get(u["id"], {})
        u["custom_fee"] = profile.get("custom_fee")
        u["class_id"] = profile.get("class_id")

    months = {}
    for f in fees_list:
        m = f.get("month") or "-"
        months.setdefault(m, {"paid": 0, "unpaid": 0})
        amt = float(f.get("amount") or 0)
        if f.get("status") == "paid":
            months[m]["paid"] += amt
        else:
            months[m]["unpaid"] += amt

    fee_labels = list(months.keys())
    fee_paid = [months[m]["paid"] for m in fee_labels]
    fee_unpaid = [months[m]["unpaid"] for m in fee_labels]
    total_paid_amount = sum(float(f.get("amount") or 0) for f in fees_list if f.get("status") == "paid")
    total_unpaid_amount = sum(float(f.get("amount") or 0) for f in fees_list if f.get("status") != "paid")
    pending_by_student = {}
    for f in fees_list:
        if f.get("status") != "paid":
            sid = f["student_user_id"]
            pending_by_student[sid] = pending_by_student.get(sid, 0) + float(f.get("amount") or 0)

    return render_template(
        "super_admin/fees.html",
        fees=fees_list,
        students=students,
        classes=classes,
        structures=structures,
        fee_labels=fee_labels,
        fee_paid=fee_paid,
        fee_unpaid=fee_unpaid,
        total_paid_amount=round(total_paid_amount, 2),
        total_unpaid_amount=round(total_unpaid_amount, 2),
        pending_by_student=pending_by_student,
    )


# =====================================================
# NOTICES
# =====================================================
@super_admin_bp.route("/notices", methods=["GET", "POST"])
@role_required("super_admin")
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
        return redirect(url_for("super_admin.notices"))

    rows = _safe_select("notices")
    users = _safe_select("users")
    umap = {u["id"]: u["name"] for u in users}

    try:
        reads = _safe_select("notice_reads")
    except Exception:
        reads = []

    total_users_by_role = {
        "all": sum(1 for u in users if u["role"] in ("student", "parent", "teacher")),
        "student": sum(1 for u in users if u["role"] == "student"),
        "parent": sum(1 for u in users if u["role"] == "parent"),
        "teacher": sum(1 for u in users if u["role"] == "teacher"),
    }

    for n in rows:
        n["posted_by"] = umap.get(n["posted_by_user_id"], "-")
        n_reads = [r for r in reads if r["notice_id"] == n["id"]]
        n["read_count"] = len(n_reads)
        target = n.get("target_role") or "all"
        n["total_target"] = total_users_by_role.get(target, 0)
        n["read_percent"] = round(n["read_count"] * 100 / n["total_target"], 1) if n["total_target"] else 0

    return render_template("super_admin/notices.html", notices=rows)


@super_admin_bp.route("/notices/edit/<int:nid>", methods=["POST"])
@role_required("super_admin")
def edit_notice(nid):
    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    target = request.form.get("target_role") or "all"
    if not title or not body:
        flash("Title and body are required.", "error")
    else:
        try:
            table("notices").update({"title": title, "body": body, "target_role": target}).eq("id", nid).execute()
            flash("Notice updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.notices"))


@super_admin_bp.route("/notices/delete/<int:nid>", methods=["POST"])
@role_required("super_admin")
def delete_notice(nid):
    try:
        table("notices").delete().eq("id", nid).execute()
        flash("Notice deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("super_admin.notices"))


@super_admin_bp.route("/notices/readers/<int:nid>")
@role_required("super_admin")
def notice_readers(nid):
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
    return render_template("super_admin/notice_readers.html", notice=notice, readers=readers)


# =====================================================
# HELPERS
# =====================================================
def _safe_select(table_name: str, **filters):
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
