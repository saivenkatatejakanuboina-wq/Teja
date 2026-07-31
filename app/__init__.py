"""Application factory for the Mini CRM."""

import os
from pathlib import Path

from flask import Flask, render_template

from app.extensions import csrf, db, login_manager
from config import config_by_name


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["default"]))

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["BACKUP_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _create_database(app)
    _seed_default_admin(app)
    _seed_sample_employee(app)
    _seed_user_permissions(app)
    _seed_settings(app)

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        """Session management: reload the user from the user ID stored in the session."""
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.activities import activities_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.companies import companies_bp
    from app.blueprints.contacts import contacts_bp
    from app.blueprints.customers import customers_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.deals import deals_bp
    from app.blueprints.followups import followups_bp
    from app.blueprints.leads import leads_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.tasks import tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(leads_bp, url_prefix="/leads")
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(followups_bp, url_prefix="/followups")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(companies_bp, url_prefix="/companies")
    app.register_blueprint(contacts_bp, url_prefix="/contacts")
    app.register_blueprint(deals_bp, url_prefix="/deals")


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_settings():
        from app.services.settings_service import get_settings

        try:
            settings = get_settings()
        except Exception:  # noqa: BLE001
            settings = None
        return {
            "app_settings": settings,
            "app_company_name": settings.company_name if settings else "Mini CRM",
            "app_theme": settings.theme if settings else "light",
            "app_currency": settings.currency if settings else "USD",
            "app_timezone": settings.timezone if settings else "UTC",
        }


def _create_database(app: Flask) -> None:
    """Create database tables automatically on startup."""
    with app.app_context():
        import app.models  # noqa: F401

        db.create_all()
        _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    """Add newly introduced columns on existing SQLite databases."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "activity_logs" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("activity_logs")}
    if "ip_address" not in columns:
        db.session.execute(text("ALTER TABLE activity_logs ADD COLUMN ip_address VARCHAR(64)"))
        db.session.commit()


def _seed_default_admin(app: Flask) -> None:
    """Ensure a default Admin account exists for first-time access."""
    from app.models import ROLE_ADMIN, User

    username = app.config.get("ADMIN_USERNAME", "admin")
    email = app.config.get("ADMIN_EMAIL", "admin@minicrm.local")
    password = app.config.get("ADMIN_PASSWORD", "admin123")

    with app.app_context():
        admin = User.query.filter_by(username=username).first()
        if admin is None:
            admin = User(
                username=username,
                email=email,
                full_name="System Admin",
                role=ROLE_ADMIN,
            )
            admin.set_password(password)
            admin.apply_role_defaults()
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Default admin account created: %s", username)
        elif admin.role != ROLE_ADMIN:
            admin.role = ROLE_ADMIN
            admin.apply_role_defaults()
            db.session.commit()


def _seed_sample_employee(app: Flask) -> None:
    """Ensure a sample Employee account exists for lead assignment demos."""
    from app.models import ROLE_EMPLOYEE, User

    with app.app_context():
        employee = User.query.filter_by(username="employee").first()
        if employee is None:
            employee = User(
                username="employee",
                email="employee@minicrm.local",
                full_name="Alex Employee",
                role=ROLE_EMPLOYEE,
            )
            employee.set_password("employee123")
            employee.apply_role_defaults()
            db.session.add(employee)
            db.session.commit()
            app.logger.info("Sample employee account created: employee")


def _seed_user_permissions(app: Flask) -> None:
    """Backfill default role permissions for users missing them."""
    from app.models import User

    with app.app_context():
        updated = 0
        for user in User.query.all():
            if not user.permissions_json or user.permissions_json == "[]":
                user.apply_role_defaults()
                updated += 1
        if updated:
            db.session.commit()
            app.logger.info("Applied default permissions to %s user(s)", updated)


def _seed_settings(app: Flask) -> None:
    """Ensure default application settings exist."""
    with app.app_context():
        from app.services.settings_service import get_settings

        get_settings()
