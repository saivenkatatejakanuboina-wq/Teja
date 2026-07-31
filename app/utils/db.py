"""Database helpers for safer commits and lookups."""

from __future__ import annotations

from flask import abort, flash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db


def get_or_404(model, entity_id: int):
    """Fetch a model by primary key or abort with 404."""
    obj = db.session.get(model, entity_id)
    if obj is None:
        abort(404)
    return obj


def commit_session(
    *,
    success_message: str | None = None,
    integrity_message: str = "Could not save — a conflicting record already exists.",
    error_message: str = "Something went wrong while saving. Please try again.",
) -> bool:
    """Commit the current session with consistent error handling.

    Returns True on success, False after rollback + flash.
    """
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(integrity_message, "danger")
        return False
    except SQLAlchemyError:
        db.session.rollback()
        flash(error_message, "danger")
        return False
    if success_message:
        flash(success_message, "success")
    return True
