"""Database seeding helpers (kept out of the app factory for clarity)."""

from __future__ import annotations

import logging

from flask import Flask

from app.extensions import db

logger = logging.getLogger(__name__)


def seed_default_admin(app: Flask) -> None:
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
            logger.info("Default admin account created: %s", username)
        elif admin.role != ROLE_ADMIN:
            admin.role = ROLE_ADMIN
            admin.apply_role_defaults()
            db.session.commit()


def seed_sample_employee(app: Flask) -> None:
    """Optional demo employee — disabled in production unless SEED_DEMO_USERS=true."""
    if not app.config.get("SEED_DEMO_USERS"):
        return

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
            logger.info("Sample employee account created: employee")


def seed_user_permissions(app: Flask) -> None:
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
            logger.info("Applied default permissions to %s user(s)", updated)


def seed_settings(app: Flask) -> None:
    with app.app_context():
        from app.services.settings_service import get_settings

        get_settings()


def seed_email_templates(app: Flask) -> None:
    with app.app_context():
        from app.models import User
        from app.services.email_service import seed_default_templates

        admin = User.query.filter_by(role="admin").first()
        created = seed_default_templates(user_id=admin.id if admin else None)
        if created:
            logger.info("Seeded %s default email template(s)", created)


def seed_whatsapp_templates(app: Flask) -> None:
    with app.app_context():
        from app.models import User
        from app.services.whatsapp_service import seed_default_templates

        admin = User.query.filter_by(role="admin").first()
        created = seed_default_templates(user_id=admin.id if admin else None)
        if created:
            logger.info("Seeded %s default WhatsApp template(s)", created)


def run_all_seeds(app: Flask) -> None:
    """Run startup seeds in a stable order."""
    seed_default_admin(app)
    seed_sample_employee(app)
    seed_user_permissions(app)
    seed_settings(app)
    seed_email_templates(app)
    seed_whatsapp_templates(app)
