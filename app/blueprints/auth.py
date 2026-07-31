"""Authentication blueprint — login, logout, register, session management."""

from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from wtforms import SubmitField

from app.extensions import db
from app.forms import LoginForm, RegisterForm
from app.models import ROLE_EMPLOYEE, User
from app.services.activity import log_activity
from app.services.admin_service import record_login_attempt
from app.utils.security import safe_redirect_target

auth_bp = Blueprint("auth", __name__)


class LogoutForm(FlaskForm):
    """CSRF-protected logout confirmation (POST only)."""

    submit = SubmitField("Sign Out")


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
            next_page = safe_redirect_target(
                request.args.get("next"),
                fallback=url_for("dashboard.index"),
            )
            return redirect(next_page)

    return render_template("auth/login.html", form=form, title="Sign In")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new Employee account when public registration is enabled."""
    if not current_app.config.get("ALLOW_PUBLIC_REGISTRATION", True):
        flash("Public registration is disabled. Ask an administrator for an account.", "warning")
        return redirect(url_for("auth.login"))

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
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already exists.", "danger")
        else:
            flash("Employee account created successfully. Please sign in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, title="Register")


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """End the current session (POST preferred for CSRF protection)."""
    form = LogoutForm()
    # Support legacy GET links once; prefer POST from the UI.
    if request.method == "GET" or form.validate_on_submit():
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
    flash("Could not sign out securely. Please try again.", "danger")
    return redirect(url_for("dashboard.index"))
