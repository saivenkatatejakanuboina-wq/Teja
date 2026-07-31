"""Admin panel: users, roles, permissions, login history."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.decorators import admin_required
from app.extensions import db
from app.forms import AdminResetPasswordForm, AdminUserForm
from app.models import (
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSIONS,
    ROLE_ADMIN,
    USER_ROLES,
    LoginHistory,
    User,
)
from app.services.activity import log_activity
from app.services.admin_service import ensure_user_permissions

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

PERM_KEYS = [key for key, _ in PERMISSIONS]


def _admin_count() -> int:
    return User.query.filter_by(role=ROLE_ADMIN, is_active=True).count()


@admin_bp.route("/")
@admin_required
def dashboard():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    admin_users = User.query.filter_by(role=ROLE_ADMIN).count()
    manager_users = User.query.filter_by(role="manager").count()
    employee_users = User.query.filter_by(role="employee").count()

    recent_logins = (
        LoginHistory.query.order_by(LoginHistory.created_at.desc()).limit(10).all()
    )
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    role_stats = [
        {"label": "Admin", "count": admin_users},
        {"label": "Manager", "count": manager_users},
        {"label": "Employee", "count": employee_users},
    ]

    return render_template(
        "admin/dashboard.html",
        title="Admin Panel",
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        role_stats=role_stats,
        recent_logins=recent_logins,
        recent_users=recent_users,
        permission_catalog=PERMISSIONS,
        role_permissions=DEFAULT_ROLE_PERMISSIONS,
    )


@admin_bp.route("/users")
@admin_required
def users():
    q = (request.args.get("q") or "").strip()
    role = (request.args.get("role") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                User.username.ilike(like),
                User.email.ilike(like),
                User.full_name.ilike(like),
            )
        )
    if role in USER_ROLES:
        query = query.filter(User.role == role)
    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(User.is_active.is_(False))

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "admin/users.html",
        title="Manage Users",
        users=pagination.items,
        pagination=pagination,
        q=q,
        role=role,
        status=status,
        roles=USER_ROLES,
    )


@admin_bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def user_create():
    form = AdminUserForm()
    if request.method == "GET":
        form.role.data = "employee"
        form.is_active.data = True
        form.permissions.data = list(DEFAULT_ROLE_PERMISSIONS["employee"])

    if form.validate_on_submit():
        if not form.password.data:
            form.password.errors.append("Password is required for new users.")
        else:
            user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                full_name=form.full_name.data.strip(),
                role=form.role.data,
                is_active=bool(form.is_active.data),
            )
            user.set_password(form.password.data)
            selected = form.permissions.data or []
            user.set_permissions([p for p in selected if p in PERM_KEYS])
            if not user.get_permissions() or form.role.data == ROLE_ADMIN:
                user.apply_role_defaults()
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Username or email already exists.", "danger")
            else:
                log_activity(
                    "user_created",
                    f"Created user {user.username} ({user.role})",
                    entity_type="user",
                    entity_id=user.id,
                    details=f"Role={user.role}; active={user.is_active}",
                )
                db.session.commit()
                flash("User created successfully.", "success")
                return redirect(url_for("admin.users"))

    return render_template(
        "admin/user_form.html",
        form=form,
        title="Create User",
        user=None,
        role_defaults=DEFAULT_ROLE_PERMISSIONS,
    )


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def user_edit(user_id: int):
    user = User.query.get_or_404(user_id)
    ensure_user_permissions(user)
    form = AdminUserForm(original_user=user, obj=user)

    if request.method == "GET":
        form.permissions.data = [
            p for p in user.get_permissions() if p in PERM_KEYS
        ]
        form.password.data = ""
        form.confirm_password.data = ""

    if form.validate_on_submit():
        was_admin = user.role == ROLE_ADMIN and user.is_active
        new_role = form.role.data
        new_active = bool(form.is_active.data)

        if was_admin and (new_role != ROLE_ADMIN or not new_active) and _admin_count() <= 1:
            flash("Cannot demote or deactivate the last active admin.", "danger")
            return render_template(
                "admin/user_form.html",
                form=form,
                title="Edit User",
                user=user,
                role_defaults=DEFAULT_ROLE_PERMISSIONS,
            )

        user.username = form.username.data.strip()
        user.email = form.email.data.strip().lower()
        user.full_name = form.full_name.data.strip()
        user.role = new_role
        user.is_active = new_active
        selected = form.permissions.data or []
        user.set_permissions([p for p in selected if p in PERM_KEYS])
        if new_role == ROLE_ADMIN:
            user.apply_role_defaults()
        if form.password.data:
            user.set_password(form.password.data)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already exists.", "danger")
        else:
            log_activity(
                "user_updated",
                f"Updated user {user.username}",
                entity_type="user",
                entity_id=user.id,
                details=f"Role={user.role}; active={user.is_active}",
            )
            db.session.commit()
            flash("User updated successfully.", "success")
            return redirect(url_for("admin.users"))

    return render_template(
        "admin/user_form.html",
        form=form,
        title="Edit User",
        user=user,
        role_defaults=DEFAULT_ROLE_PERMISSIONS,
    )


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def user_toggle(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.users"))

    if user.role == ROLE_ADMIN and user.is_active and _admin_count() <= 1:
        flash("Cannot deactivate the last active admin.", "danger")
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active
    state = "activated" if user.is_active else "deactivated"
    log_activity(
        f"user_{state}",
        f"{user.username} {state}",
        entity_type="user",
        entity_id=user.id,
    )
    db.session.commit()
    flash(f"User {state}.", "success")
    return redirect(request.referrer or url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["GET", "POST"])
@admin_required
def user_reset_password(user_id: int):
    user = User.query.get_or_404(user_id)
    form = AdminResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        log_activity(
            "user_password_reset",
            f"Password reset for {user.username}",
            entity_type="user",
            entity_id=user.id,
        )
        db.session.commit()
        flash(f"Password reset for {user.username}.", "success")
        return redirect(url_for("admin.users"))
    return render_template(
        "admin/reset_password.html",
        form=form,
        user=user,
        title="Reset Password",
    )


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def user_delete(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.users"))

    if user.role == ROLE_ADMIN and user.is_active and _admin_count() <= 1:
        flash("Cannot delete the last active admin.", "danger")
        return redirect(url_for("admin.users"))

    username = user.username
    log_activity(
        "user_deleted",
        f"Deleted user {username}",
        entity_type="user",
        entity_id=user_id,
    )
    try:
        db.session.delete(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            f"Cannot delete {username} because related CRM records still exist. "
            "Deactivate the account instead.",
            "danger",
        )
        return redirect(url_for("admin.users"))
    flash(f"User {username} deleted.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/roles")
@admin_required
def roles():
    counts = {role: User.query.filter_by(role=role).count() for role in USER_ROLES}
    return render_template(
        "admin/roles.html",
        title="Roles & Permissions",
        roles=USER_ROLES,
        role_permissions=DEFAULT_ROLE_PERMISSIONS,
        permission_catalog=PERMISSIONS,
        counts=counts,
    )


@admin_bp.route("/login-history")
@admin_required
def login_history():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = LoginHistory.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                LoginHistory.username_attempted.ilike(like),
                LoginHistory.ip_address.ilike(like),
            )
        )
    if status in {"success", "failed"}:
        query = query.filter(LoginHistory.status == status)

    pagination = query.order_by(LoginHistory.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    success_count = (
        db.session.query(func.count(LoginHistory.id))
        .filter(LoginHistory.status == "success")
        .scalar()
        or 0
    )
    failed_count = (
        db.session.query(func.count(LoginHistory.id))
        .filter(LoginHistory.status == "failed")
        .scalar()
        or 0
    )

    return render_template(
        "admin/login_history.html",
        title="Login History",
        entries=pagination.items,
        pagination=pagination,
        q=q,
        status=status,
        success_count=success_count,
        failed_count=failed_count,
    )
