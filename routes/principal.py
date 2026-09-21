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

    return render_template("principal/reports.html", att_rows=att_rows, fee_summary=fee_summary)


@principal_bp.route("/notices", methods=["GET", "POST"])
@role_required("principal")
def notices():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        target = request.form.get("target_role") or "all"
        if not title or not body:
            flash("Title and body required.", "error")
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
        n["can_edit"] = (n["posted_by_user_id"] == session["user_id"])
        n_reads = [r for r in reads if r["notice_id"] == n["id"]]
        n["read_count"] = len(n_reads)
        target = n.get("target_role") or "all"
        n["total_target"] = total_users_by_role.get(target, 0)
        n["read_percent"] = round(n["read_count"] * 100 / n["total_target"], 1) if n["total_target"] else 0

    return render_template("principal/notices.html", notices=rows)


@principal_bp.route("/notices/edit/<int:nid>", methods=["POST"])
@role_required("principal")
def edit_notice(nid):
    existing = table("notices").select("*").eq("id", nid).limit(1).execute().data
    if not existing or existing[0]["posted_by_user_id"] != session["user_id"]:
        flash("You can only edit your own notices.", "error")
        return redirect(url_for("principal.notices"))

    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    target = request.form.get("target_role") or "all"
    if not title or not body:
        flash("Required.", "error")
    else:
        try:
            table("notices").update({"title": title, "body": body, "target_role": target}).eq("id", nid).execute()
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


@principal_bp.route("/notices/readers/<int:nid>")
@role_required("principal")
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
    except Exception:
        pass
    return render_template("principal/notice_readers.html", notice=notice, readers=readers)


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
