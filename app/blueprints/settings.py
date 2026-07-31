"""Settings module — company, SMTP, theme, backup/restore, profile, password."""

from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from app.decorators import admin_required
from app.extensions import db
from app.forms import (
    ChangePasswordForm,
    CompanySettingsForm,
    ProfileForm,
    RestoreDatabaseForm,
    SMTPSettingsForm,
    ThemeSettingsForm,
)
from app.services import settings_service

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
@login_required
def index():
    """Settings hub with tabbed forms."""
    settings = settings_service.get_settings()
    company_form = CompanySettingsForm(obj=settings)
    smtp_form = SMTPSettingsForm(obj=settings)
    theme_form = ThemeSettingsForm(obj=settings)
    profile_form = ProfileForm(original_user=current_user, obj=current_user)
    password_form = ChangePasswordForm()
    restore_form = RestoreDatabaseForm()
    backups = settings_service.list_backups() if current_user.is_admin else []
    active_tab = request.args.get("tab", "company")

    return render_template(
        "settings/index.html",
        title="Settings",
        settings=settings,
        company_form=company_form,
        smtp_form=smtp_form,
        theme_form=theme_form,
        profile_form=profile_form,
        password_form=password_form,
        restore_form=restore_form,
        backups=backups,
        active_tab=active_tab,
    )


@settings_bp.route("/company", methods=["POST"])
@login_required
@admin_required
def save_company():
    settings = settings_service.get_settings()
    form = CompanySettingsForm()
    if form.validate_on_submit():
        settings.company_name = form.company_name.data.strip()
        settings.timezone = form.timezone.data
        settings.currency = form.currency.data
        if form.logo.data:
            try:
                filename = settings_service.save_logo(form.logo.data)
                if filename:
                    # Remove previous logo file if present
                    if settings.logo_filename:
                        old = Path(current_app.config["UPLOAD_FOLDER"]) / settings.logo_filename
                        if old.exists():
                            old.unlink()
                    settings.logo_filename = filename
            except ValueError as exc:
                flash(str(exc), "danger")
                return redirect(url_for("settings.index", tab="company"))
        db.session.commit()
        flash("Company settings saved.", "success")
    else:
        flash("Please correct the company settings form.", "danger")
    return redirect(url_for("settings.index", tab="company"))


@settings_bp.route("/smtp", methods=["POST"])
@login_required
@admin_required
def save_smtp():
    settings = settings_service.get_settings()
    form = SMTPSettingsForm()
    if form.validate_on_submit():
        settings.smtp_host = form.smtp_host.data.strip() if form.smtp_host.data else None
        settings.smtp_port = form.smtp_port.data or 587
        settings.smtp_username = (
            form.smtp_username.data.strip() if form.smtp_username.data else None
        )
        if form.smtp_password.data:
            settings.smtp_password = form.smtp_password.data
        settings.smtp_from_email = (
            form.smtp_from_email.data.strip() if form.smtp_from_email.data else None
        )
        settings.smtp_use_tls = bool(form.smtp_use_tls.data)
        db.session.commit()
        flash("SMTP settings saved.", "success")
    else:
        flash("Please correct the SMTP settings form.", "danger")
    return redirect(url_for("settings.index", tab="smtp"))


@settings_bp.route("/theme", methods=["POST"])
@login_required
@admin_required
def save_theme():
    settings = settings_service.get_settings()
    form = ThemeSettingsForm()
    if form.validate_on_submit():
        settings.theme = form.theme.data
        db.session.commit()
        flash("Theme updated.", "success")
    else:
        flash("Please choose a valid theme.", "danger")
    return redirect(url_for("settings.index", tab="theme"))


@settings_bp.route("/profile", methods=["POST"])
@login_required
def save_profile():
    form = ProfileForm(original_user=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.email = form.email.data.strip().lower()
        current_user.username = form.username.data.strip()
        db.session.commit()
        flash("Profile updated.", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.replace('_', ' ').title()}: {error}", "danger")
    return redirect(url_for("settings.index", tab="profile"))


@settings_bp.route("/password", methods=["POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password changed successfully.", "success")
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
    return redirect(url_for("settings.index", tab="password"))


@settings_bp.route("/backup", methods=["POST"])
@login_required
@admin_required
def backup_database():
    try:
        path = settings_service.create_backup()
        flash(f"Backup created: {path.name}", "success")
    except Exception as exc:  # noqa: BLE001
        flash(f"Backup failed: {exc}", "danger")
    return redirect(url_for("settings.index", tab="backup"))


@settings_bp.route("/backup/download/<path:filename>")
@login_required
@admin_required
def download_backup(filename: str):
    folder = Path(current_app.config["BACKUP_FOLDER"]).resolve()
    target = (folder / filename).resolve()
    if not str(target).startswith(str(folder)) or not target.exists():
        flash("Backup file not found.", "danger")
        return redirect(url_for("settings.index", tab="backup"))
    return send_file(target, as_attachment=True, download_name=target.name)


@settings_bp.route("/restore", methods=["POST"])
@login_required
@admin_required
def restore_database():
    form = RestoreDatabaseForm()
    if form.validate_on_submit():
        try:
            settings_service.restore_database(form.backup_file.data)
            flash(
                "Database restored successfully. Please sign in again if prompted.",
                "success",
            )
        except Exception as exc:  # noqa: BLE001
            flash(f"Restore failed: {exc}", "danger")
    else:
        flash("Please upload a valid .db backup file.", "danger")
    return redirect(url_for("settings.index", tab="backup"))
