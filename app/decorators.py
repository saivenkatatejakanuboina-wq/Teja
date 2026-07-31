"""Route protection helpers."""

from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def login_required_active(view):
    """Ensure the user is authenticated and the account is active."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
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
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def employee_required(view):
    """Allow Admin or Employee accounts (any authenticated active user)."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role not in ("admin", "manager", "employee") or not current_user.is_active:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
