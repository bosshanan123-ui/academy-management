"""
app.py
Flask application factory + entrypoint.
Vercel expects a module-level `app` variable.
"""
from flask import Flask, redirect, url_for, session, render_template

from config import Config


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.super_admin import super_admin_bp
    from routes.principal import principal_bp
    from routes.teacher import teacher_bp
    from routes.student import student_bp
    from routes.parent import parent_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp, url_prefix="/super-admin")
    app.register_blueprint(principal_bp, url_prefix="/principal")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(parent_bp, url_prefix="/parent")

    @app.route("/")
    def index():
        """Redirect to dashboard based on session role."""
        role = session.get("role")
        if not role:
            return redirect(url_for("auth.login"))
        return redirect(_dashboard_for_role(role))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("base.html", error_message="404 — Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("base.html", error_message="500 — Server error"), 500

    return app

    @app.route("/offline")
    def offline():
        """Offline fallback page for PWA."""
        from flask import send_from_directory
        return send_from_directory("static", "offline.html")

def _dashboard_for_role(role: str) -> str:
    """Return the dashboard endpoint for a given role."""
    mapping = {
        "super_admin": "super_admin.dashboard",
        "principal": "principal.dashboard",
        "teacher": "teacher.dashboard",
        "student": "student.dashboard",
        "parent": "parent.dashboard",
    }
    return url_for(mapping.get(role, "auth.login"))


# Module-level app for gunicorn / Vercel
app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
