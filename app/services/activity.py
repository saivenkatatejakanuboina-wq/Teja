"""Activity log helpers."""

from __future__ import annotations

from flask import Request, has_request_context, request
from flask_login import current_user

from app.extensions import db
from app.models import ActivityLog


def _client_ip(req: Request | None = None) -> str | None:
    req = req or (request if has_request_context() else None)
    if req is None:
        return None
    forwarded = req.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or None
    return (req.remote_addr or "")[:64] or None


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
    ip_address: str | None = None,
    request: Request | None = None,
) -> ActivityLog:
    """Persist an activity log entry for an action."""
    resolved_user_id = user_id
    if resolved_user_id is None and has_request_context() and current_user.is_authenticated:
        resolved_user_id = current_user.id
    if resolved_user_id is None:
        raise ValueError("user_id is required to log activity")

    entry = ActivityLog(
        action=action,
        message=message,
        details=details,
        ip_address=ip_address if ip_address is not None else _client_ip(request),
        lead_id=lead_id,
        customer_id=customer_id,
        entity_type=entity_type,
        entity_id=entity_id
        if entity_id is not None
        else (customer_id if customer_id is not None else lead_id),
        user_id=resolved_user_id,
    )
    db.session.add(entry)
    return entry


def activity_filter_clause(filter_key: str):
    """Map UI filter keys to action/entity_type pairs."""
    mapping = {
        "login": ("login", "auth"),
        "logout": ("logout", "auth"),
        "lead_created": ("created", "lead"),
        "lead_updated": ("updated", "lead"),
        "lead_deleted": ("deleted", "lead"),
        "customer_created": ("created", "customer"),
        "task_created": ("created", "task"),
        "task_completed": ("completed", "task"),
    }
    return mapping.get(filter_key)
