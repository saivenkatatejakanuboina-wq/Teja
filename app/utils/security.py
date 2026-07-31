"""Security helpers for redirects and request sanitization."""

from __future__ import annotations

from urllib.parse import urlparse

from flask import request


def safe_redirect_target(candidate: str | None, *, fallback: str) -> str:
    """Return a same-origin relative path, otherwise fallback.

    Prevents open redirects via Referer / next parameters.
    """
    if not candidate:
        return fallback
    parsed = urlparse(candidate)
    if parsed.netloc or parsed.scheme:
        return fallback
    if not candidate.startswith("/"):
        return fallback
    if candidate.startswith("//"):
        return fallback
    return candidate


def safe_referrer_or(fallback: str) -> str:
    """Use request.referrer only when it is a relative/same-app path."""
    return safe_redirect_target(request.referrer, fallback=fallback)


def whitelist_external_redirect(url: str | None, *, allowed_hosts: set[str]) -> str | None:
    """Allow only absolute redirects to trusted hosts (e.g. wa.me)."""
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    host = (parsed.hostname or "").lower()
    if host not in allowed_hosts:
        return None
    return url
