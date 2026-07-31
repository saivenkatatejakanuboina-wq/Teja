"""Helpers for application settings, uploads, and database backup/restore."""

from __future__ import annotations

import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import AppSettings


def get_settings() -> AppSettings:
    """Return the singleton settings row, creating defaults if needed."""
    settings = AppSettings.query.first()
    if settings is None:
        settings = AppSettings(
            company_name="Mini CRM",
            timezone="UTC",
            currency="USD",
            theme="light",
            smtp_port=587,
            smtp_use_tls=True,
        )
        db.session.add(settings)
        db.session.commit()
    return settings


def ensure_directories() -> None:
    Path(current_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(current_app.config["BACKUP_FOLDER"]).mkdir(parents=True, exist_ok=True)


def _allowed_logo(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_LOGO_EXTENSIONS"]


def save_logo(file_storage: FileStorage) -> str | None:
    """Save an uploaded logo and return the stored filename."""
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed_logo(file_storage.filename):
        raise ValueError("Unsupported logo file type.")

    ensure_directories()
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower()
    filename = f"logo_{uuid.uuid4().hex[:10]}.{ext}"
    path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    file_storage.save(path)
    return filename


def resolve_db_path() -> Path:
    """Resolve the active SQLite database file path."""
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("sqlite:///"):
        raw = uri.replace("sqlite:///", "", 1)
        path = Path(raw)
        if not path.is_absolute():
            # Flask-SQLAlchemy commonly stores relative sqlite files under instance/
            instance_candidate = Path(current_app.instance_path) / path.name
            if instance_candidate.exists() or not path.exists():
                return instance_candidate
            return path if path.is_absolute() else Path.cwd() / path
        return path
    raise RuntimeError("Database backup/restore is only supported for SQLite.")


def create_backup() -> Path:
    """Copy the SQLite database into the backups folder and return the path."""
    ensure_directories()
    db_path = resolve_db_path()
    if not db_path.exists():
        # Ensure DB file exists by committing metadata
        db.session.commit()
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = Path(current_app.config["BACKUP_FOLDER"]) / f"crm_backup_{stamp}.db"

    # Checkpoint WAL so the copy is consistent
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA wal_checkpoint(FULL);")
    except sqlite3.Error:
        pass

    shutil.copy2(db_path, dest)
    return dest


def list_backups() -> list[dict]:
    ensure_directories()
    folder = Path(current_app.config["BACKUP_FOLDER"])
    files = sorted(folder.glob("crm_backup_*.db"), reverse=True)
    result = []
    for path in files:
        stat = path.stat()
        result.append(
            {
                "name": path.name,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.utcfromtimestamp(stat.st_mtime),
            }
        )
    return result


def restore_database(file_storage: FileStorage) -> None:
    """Replace the active SQLite database with an uploaded backup."""
    if not file_storage or not file_storage.filename:
        raise ValueError("No backup file provided.")

    ensure_directories()
    filename = secure_filename(file_storage.filename)
    if not filename.lower().endswith((".db", ".sqlite")):
        raise ValueError("Invalid backup file type.")

    temp_path = Path(current_app.config["BACKUP_FOLDER"]) / f"restore_upload_{uuid.uuid4().hex}.db"
    file_storage.save(temp_path)

    # Validate SQLite header
    with open(temp_path, "rb") as handle:
        header = handle.read(16)
    if not header.startswith(b"SQLite format 3"):
        temp_path.unlink(missing_ok=True)
        raise ValueError("Uploaded file is not a valid SQLite database.")

    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Close connections before replacing the file
    db.session.remove()
    db.engine.dispose()

    # Keep a safety copy of the current DB
    if db_path.exists():
        safety = (
            Path(current_app.config["BACKUP_FOLDER"])
            / f"pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        )
        shutil.copy2(db_path, safety)

    shutil.copy2(temp_path, db_path)
    temp_path.unlink(missing_ok=True)

    # Dispose again so new connections open against restored file
    db.engine.dispose()
