"""Authentication blueprint — login, logout, register, session management."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from urllib.parse import urlparse

from app.extensions import db
from app.forms import LoginForm, RegisterForm
from app.models import ROLE_EMPLOYEE, User

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
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password.", "danger")
        elif not user.is_active:
            flash("Your account is inactive. Contact an administrator.", "warning")
        else:
            login_user(user, remember=form.remember_me.data)
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
        db.session.add(user)
        db.session.commit()
        flash("Employee account created successfully. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, title="Register")


@auth_bp.route("/logout")
@login_required
def logout():
    """End the current session and return to the login page."""
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
