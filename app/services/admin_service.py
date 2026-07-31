"""Helpers for the admin panel."""

from __future__ import annotations

from flask import Request

from app.extensions import db
from app.models import DEFAULT_ROLE_PERMISSIONS, LoginHistory, User


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or None
    return (request.remote_addr or "")[:64] or None


def record_login_attempt(
    *,
    username: str,
    status: str,
    request: Request,
    user: User | None = None,
) -> LoginHistory:
    entry = LoginHistory(
        user_id=user.id if user else None,
        username_attempted=(username or "")[:80],
        status=status,
        ip_address=client_ip(request),
        user_agent=(request.headers.get("User-Agent") or "")[:255] or None,
    )
    db.session.add(entry)
    return entry


def ensure_user_permissions(user: User) -> None:
    if not user.permissions_json:
        user.apply_role_defaults()


def sync_role_permissions(role: str) -> list[str]:
    return list(DEFAULT_ROLE_PERMISSIONS.get(role, DEFAULT_ROLE_PERMISSIONS["employee"]))
