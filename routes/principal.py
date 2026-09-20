"""
routes/principal.py
Principal: read-only overview + notices (post/edit/delete).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from utils.supabase_client import table
from utils.decorators import role_required

principal_bp = Blueprint("principal", __name__)


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

    class_labels = [c["name"] for c in classes]
    students_p = _safe_select("students")
    class_counts = [
        sum(1 for s in students_p if s.get("class_id") == c["id"]) for c in classes
    ]

    return render_template(
        "principal/dashboard.html",
        stats={
            "students": len(students),
            "teachers": len(teachers),
            "classes": len(classes),
            "sections": len(sections),
            "subjects": len(subjects),
            "collected": round(collected, 2),
        },
        class_labels=class_labels,
        class_counts=class_counts,
    )


@principal_bp.route("/reports")
@role_required("principal")
def reports():
    attendance = _safe_select("attendance")
    marks = _safe_select("marks")
    fees = _safe_select("fees")
    users = _safe_select("users")
    umap = {u["id"]: u for u in users}

    per_student = {}
    for a in attendance:
        sid = a["student_user_id"]
        per_student.setdefault(sid, {"P": 0, "A": 0, "L": 0})
        per_student[sid][a["status"]] = per_student[sid].get(a["status"], 0) + 1

    att_rows = []
    for sid, counts in per_student.items():
        u = umap.get(sid, {})
        total = counts["P"] + counts["A"] + counts["L"] or 1
        att_rows.append({
            "name": u.get("name", "-"),
            "roll": u.get("roll_number", "-"),
            "present": counts["P"],
            "absent": counts["A"],
            "leave": counts["L"],
            "percent": round(counts["P"] * 100 / total, 1),
        })

    fee_summary = {}
    for f in fees:
        m = f.get("month") or "-"
        fee_summary.setdefault(m, {"paid": 0, "unpaid": 0})
        if f.get("status") == "paid":
            fee_summary[m]["paid"] += float(f.get("amount") or 0)
        else:
            fee_summary[m]["unpaid"] += float(f.get("amount") or 0)

    return render_template(
        "principal/reports.html",
        att_rows=att_rows,
        fee_summary=fee_summary,
    )


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

    rows = _safe_select("notices")
    users = _safe_select("users")
    umap = {u["id"]: u["name"] for u in users}
    for n in rows:
        n["posted_by"] = umap.get(n["posted_by_user_id"], "-")
        n["can_edit"] = (n["posted_by_user_id"] == session["user_id"])
    return render_template("principal/notices.html", notices=rows)


@principal_bp.route("/notices/edit/<int:nid>", methods=["POST"])
@role_required("principal")
def edit_notice(nid):
    # Only allow editing own notices
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
        try:
            table("notices").update({
                "title": title,
                "body": body,
                "target_role": target,
            }).eq("id", nid).execute()
            flash("Notice updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("principal.notices"))


@principal_bp.route("/notices/delete/<int:nid>", methods=["POST"])
@role_required("principal")
def delete_notice(nid):
    existing = table("notices").select("*").eq("id", nid).limit(1).execute().data
    if not existing or existing[0]["posted_by_user_id"] != session["user_id"]:
        flash("You can only delete your own notices.", "error")
        return redirect(url_for("principal.notices"))
    try:
        table("notices").delete().eq("id", nid).execute()
        flash("Notice deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("principal.notices"))


def _safe_select(table_name: str, **filters):
    try:
        q = table(table_name).select("*")
        for k, v in filters.items():
            q = q.eq(k, v)
        return q.execute().data or []
    except Exception:
        return []
