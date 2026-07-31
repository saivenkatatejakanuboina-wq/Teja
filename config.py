"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration for the Mini CRM application."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'crm.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Reduce idle connection chatter; useful when moving to Postgres later.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    WTF_CSRF_ENABLED = True
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 14  # 14 days
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Uploads & backups — SVG disallowed to reduce stored XSS risk
    UPLOAD_FOLDER = str(BASE_DIR / "app" / "static" / "uploads")
    BACKUP_FOLDER = str(BASE_DIR / "backups")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
    ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Default Admin account (seeded on startup if missing)
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@minicrm.local")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    # Feature flags
    MAIL_SUPPRESS_SEND = _env_bool("MAIL_SUPPRESS_SEND", False)
    # Seed demo employee account (development convenience)
    SEED_DEMO_USERS = _env_bool("SEED_DEMO_USERS", True)
    # Public self-registration (disable in production)
    ALLOW_PUBLIC_REGISTRATION = _env_bool("ALLOW_PUBLIC_REGISTRATION", True)


class DevelopmentConfig(Config):
    DEBUG = True
    SEED_DEMO_USERS = _env_bool("SEED_DEMO_USERS", True)
    ALLOW_PUBLIC_REGISTRATION = _env_bool("ALLOW_PUBLIC_REGISTRATION", True)


class ProductionConfig(Config):
    """Hardened settings for deployment behind a reverse proxy / gunicorn."""

    DEBUG = False
    # Never seed weak demo accounts unless explicitly requested
    SEED_DEMO_USERS = _env_bool("SEED_DEMO_USERS", False)
    ALLOW_PUBLIC_REGISTRATION = _env_bool("ALLOW_PUBLIC_REGISTRATION", False)

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = "https"

    def __init__(self) -> None:  # pragma: no cover - config object style
        pass

    @classmethod
    def validate(cls) -> None:
        """Fail fast when production secrets are missing or unsafe."""
        secret = os.getenv("SECRET_KEY", "")
        if not secret or secret == "dev-secret-key-change-me":
            raise RuntimeError(
                "Production requires a strong SECRET_KEY environment variable."
            )
        password = os.getenv("ADMIN_PASSWORD", "")
        if not password or password == "admin123":
            raise RuntimeError(
                "Production requires ADMIN_PASSWORD to be set to a non-default value."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
