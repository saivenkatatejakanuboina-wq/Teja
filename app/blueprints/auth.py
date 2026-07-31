"""Authentication blueprint — login, logout, register, session management."""

from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm, RegisterForm
from app.models import ROLE_EMPLOYEE, User
from app.services.activity import log_activity
from app.services.admin_service import record_login_attempt

auth_bp = Blueprint("auth", __name__)


def _safe_next_url(next_url: str | None) -> str | None:
    """Only allow relative redirects within the app."""
    if not next_url:
        return None
    parsed = urlparse(next_url)
    if parsed.netloc or parsed.scheme:
        return None
    if not next_url.startswith("/"):
        return None
    return next_url


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Log in an Admin or Employee and redirect to the dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(form.password.data):
            record_login_attempt(
                username=username,
                status="failed",
                request=request,
                user=user,
            )
            db.session.commit()
            flash("Invalid username or password.", "danger")
        elif not user.is_active:
            record_login_attempt(
                username=username,
                status="failed",
                request=request,
                user=user,
            )
            db.session.commit()
            flash("Your account is inactive. Contact an administrator.", "warning")
        else:
            login_user(user, remember=form.remember_me.data)
            user.last_login_at = datetime.now(timezone.utc)
            record_login_attempt(
                username=username,
                status="success",
                request=request,
                user=user,
            )
            log_activity(
                "login",
                f"{user.full_name} signed in",
                entity_type="auth",
                entity_id=user.id,
                user_id=user.id,
                request=request,
            )
            db.session.commit()
            flash(f"Welcome back, {user.full_name}! ({user.role_label})", "success")
            next_page = _safe_next_url(request.args.get("next"))
            return redirect(next_page or url_for("dashboard.index"))

    return render_template("auth/login.html", form=form, title="Sign In")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new Employee account (Admins are seeded separately)."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
            role=ROLE_EMPLOYEE,
        )
        user.set_password(form.password.data)
        user.apply_role_defaults()
        db.session.add(user)
        db.session.commit()
        flash("Employee account created successfully. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, title="Register")


@auth_bp.route("/logout")
@login_required
def logout():
    """End the current session and return to the login page."""
    user = current_user._get_current_object()
    log_activity(
        "logout",
        f"{user.full_name} signed out",
        entity_type="auth",
        entity_id=user.id,
        user_id=user.id,
        request=request,
    )
    db.session.commit()
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
