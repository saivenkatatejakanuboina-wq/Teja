"""Application factory for the Mini CRM."""

import os

from flask import Flask, render_template

from app.extensions import csrf, db, login_manager
from config import config_by_name


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["default"]))

    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _create_database(app)

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.auth import auth_bp
    from app.blueprints.companies import companies_bp
    from app.blueprints.contacts import contacts_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.deals import deals_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
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


def _create_database(app: Flask) -> None:
    """Create database tables automatically on startup."""
    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()
