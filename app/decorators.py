"""Route protection helpers (authn / authz)."""

from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def login_required_active(view):
    """Ensure the user is authenticated and the account is still active."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=None))
        if not current_user.is_active:
            flash("Your account is inactive. Contact an administrator.", "danger")
            return redirect(url_for("auth.logout"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Restrict a route to Admin accounts only."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_active:
            flash("Your account is inactive. Contact an administrator.", "danger")
            return redirect(url_for("auth.logout"))
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def employee_required(view):
    """Allow any authenticated active CRM role (admin / manager / employee)."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role not in ("admin", "manager", "employee") or not current_user.is_active:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def permission_required(permission: str):
    """Require a named permission (admins always pass via User.has_permission)."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not current_user.is_active:
                flash("Your account is inactive. Contact an administrator.", "danger")
                return redirect(url_for("auth.logout"))
            if not current_user.has_permission(permission):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
