"""
utils/decorators.py
Route protection decorators.
"""
from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    """Require a logged-in user."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Require the session role to be one of `roles`."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in first.", "error")
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                flash("You are not authorized to view that page.", "error")
                return redirect(url_for("auth.login"))
            return view(*args, **kwargs)
        return wrapper
    return decorator