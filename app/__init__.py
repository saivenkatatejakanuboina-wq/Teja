"""Application factory for the Mini CRM."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, render_template

from app.extensions import csrf, db, login_manager
from config import ProductionConfig, config_by_name

logger = logging.getLogger(__name__)


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application (factory pattern)."""
    app = Flask(__name__)

    env_name = config_name or os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "development"
    config_obj = config_by_name.get(env_name, config_by_name["default"])
    app.config.from_object(config_obj)

    # Fail fast on unsafe production secrets
    if env_name == "production":
        ProductionConfig.validate()

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["BACKUP_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _register_healthchecks(app)
    _create_database(app)

    from app.seed import run_all_seeds

    run_all_seeds(app)

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        """Reload the authenticated user from the session user id."""
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.activities import activities_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.companies import companies_bp
    from app.blueprints.contacts import contacts_bp
    from app.blueprints.csv_io import csv_bp
    from app.blueprints.customers import customers_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.deals import deals_bp
    from app.blueprints.emails import emails_bp
    from app.blueprints.followups import followups_bp
    from app.blueprints.leads import leads_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.tasks import tasks_bp
    from app.blueprints.whatsapp import whatsapp_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(csv_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(whatsapp_bp)
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

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_settings():
        from sqlalchemy.exc import SQLAlchemyError

        from app.services.settings_service import get_settings

        try:
            settings = get_settings()
        except SQLAlchemyError:
            settings = None
        return {
            "app_settings": settings,
            "app_company_name": settings.company_name if settings else "Mini CRM",
            "app_theme": settings.theme if settings else "light",
            "app_currency": settings.currency if settings else "USD",
            "app_timezone": settings.timezone if settings else "UTC",
            "allow_public_registration": app.config.get("ALLOW_PUBLIC_REGISTRATION", True),
        }


def _register_healthchecks(app: Flask) -> None:
    """Lightweight endpoints for load balancers and uptime checks."""

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/ready")
    def ready():
        from sqlalchemy import text

        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({"status": "ready"}), 200
        except Exception:  # noqa: BLE001 — surface unreadiness without stack traces
            logger.exception("Readiness check failed")
            return jsonify({"status": "unavailable"}), 503


def _create_database(app: Flask) -> None:
    """Create database tables automatically on startup."""
    with app.app_context():
        import app.models  # noqa: F401 — register models with metadata

        db.create_all()
        _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    """Best-effort additive schema patches for existing SQLite databases.

    Prefer Flask-Migrate for non-trivial production schema changes.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    table_columns = {
        table: {col["name"] for col in inspector.get_columns(table)}
        for table in inspector.get_table_names()
    }

    alterations = {
        "activity_logs": [("ip_address", "VARCHAR(64)")],
        "leads": [("whatsapp_number", "VARCHAR(40)")],
        "customers": [("whatsapp_number", "VARCHAR(40)")],
        "app_settings": [
            ("whatsapp_provider", "VARCHAR(40) DEFAULT 'click_to_chat'"),
            ("whatsapp_api_base_url", "VARCHAR(255)"),
            ("whatsapp_api_token", "VARCHAR(512)"),
            ("whatsapp_phone_number_id", "VARCHAR(120)"),
            ("whatsapp_business_account_id", "VARCHAR(120)"),
        ],
    }

    changed = False
    for table, columns in alterations.items():
        existing = table_columns.get(table)
        if existing is None:
            continue
        for name, col_type in columns:
            if name not in existing:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {col_type}"))
                changed = True
    if changed:
        db.session.commit()
