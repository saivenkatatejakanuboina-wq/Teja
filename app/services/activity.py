"""Activity log helpers."""

from flask_login import current_user

from app.extensions import db
from app.models import ActivityLog


def log_activity(
    action: str,
    message: str,
    *,
    lead_id: int | None = None,
    customer_id: int | None = None,
    entity_type: str = "lead",
    entity_id: int | None = None,
    details: str | None = None,
    user_id: int | None = None,
) -> ActivityLog:
    """Persist an activity log entry for an action."""
    entry = ActivityLog(
        action=action,
        message=message,
        details=details,
        lead_id=lead_id,
        customer_id=customer_id,
        entity_type=entity_type,
        entity_id=entity_id
        if entity_id is not None
        else (customer_id if customer_id is not None else lead_id),
        user_id=user_id or current_user.id,
    )
    db.session.add(entry)
    return entry
