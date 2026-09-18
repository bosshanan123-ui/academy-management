"""
routes/auth.py
Login / logout. Role is auto-detected from roll number prefix.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash
)

from utils.supabase_client import table
from utils.password_utils import verify_password
from config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Single login page for all roles."""
    if session.get("user_id"):
        return redirect(_dashboard_for_role(session["role"]))

    if request.method == "POST":
        roll_number = (request.form.get("roll_number") or "").strip().upper()
        password = request.form.get("password") or ""

        if not roll_number or not password:
            flash("Roll number and password are required.", "error")
            return render_template("login.html", app_name=Config.APP_NAME)

        try:
            res = table("users").select("*").eq("roll_number", roll_number).limit(1).execute()
            rows = res.data or []
        except Exception as e:
            flash(f"Database error: {e}", "error")
            return render_template("login.html", app_name=Config.APP_NAME)

        if not rows:
            flash("Invalid roll number or password.", "error")
            return render_template("login.html", app_name=Config.APP_NAME)

        user = rows[0]
        if not user.get("is_active", True):
            flash("Your account is disabled.", "error")
            return render_template("login.html", app_name=Config.APP_NAME)

        if not verify_password(password, user["password_hash"]):
            flash("Invalid roll number or password.", "error")
            return render_template("login.html", app_name=Config.APP_NAME)

        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["name"] = user["name"]
        session["roll_number"] = user["roll_number"]

        flash(f"Welcome, {user['name']}!", "success")
        return redirect(_dashboard_for_role(user["role"]))

    return render_template("login.html", app_name=Config.APP_NAME)


@auth_bp.route("/logout")
def logout():
    """Clear session and go to login."""
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


def _dashboard_for_role(role: str) -> str:
    mapping = {
        "super_admin": "super_admin.dashboard",
        "principal": "principal.dashboard",
        "teacher": "teacher.dashboard",
        "student": "student.dashboard",
        "parent": "parent.dashboard",
    }
    return url_for(mapping.get(role, "auth.login"))