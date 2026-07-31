"""SMTP email: compose to leads, templates, and sent history."""

from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.forms import ComposeEmailForm, EmailTemplateForm
from app.models import EmailMessage, EmailTemplate, Lead
from app.services import email_service

emails_bp = Blueprint("emails", __name__, url_prefix="/emails")


def _populate_compose_form(form: ComposeEmailForm, selected_lead: Lead | None = None) -> None:
    leads = Lead.query.order_by(Lead.name.asc()).all()
    form.lead_id.choices = [(0, "— Select lead —")] + [
        (lead.id, f"{lead.name}" + (f" <{lead.email}>" if lead.email else " (no email)"))
        for lead in leads
    ]
    templates = (
        EmailTemplate.query.filter_by(is_active=True)
        .order_by(EmailTemplate.name.asc())
        .all()
    )
    form.template_id.choices = [(0, "— Blank / custom —")] + [
        (tpl.id, tpl.name) for tpl in templates
    ]
    if selected_lead and request.method == "GET":
        form.lead_id.data = selected_lead.id
        form.to_email.data = selected_lead.email or ""
        if not form.subject.data:
            form.subject.data = f"Hello {selected_lead.name}"


@emails_bp.route("/")
@login_required
def index():
    """Email history (sent / failed)."""
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = EmailMessage.query
    if status in {"sent", "failed", "queued"}:
        query = query.filter(EmailMessage.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                EmailMessage.to_email.ilike(like),
                EmailMessage.to_name.ilike(like),
                EmailMessage.subject.ilike(like),
            )
        )

    pagination = query.order_by(EmailMessage.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    settings_ready = email_service.smtp_configured()

    return render_template(
        "emails/history.html",
        title="Email History",
        messages=pagination.items,
        pagination=pagination,
        q=q,
        status=status,
        smtp_ready=settings_ready,
        smtp_message=email_service.smtp_status_message(),
    )


@emails_bp.route("/compose", methods=["GET", "POST"])
@login_required
def compose():
    """Bootstrap compose window for sending email to a lead."""
    lead_id = request.args.get("lead_id", type=int) or request.form.get("lead_id", type=int)
    lead = db.session.get(Lead, lead_id) if lead_id else None
    form = ComposeEmailForm()
    _populate_compose_form(form, selected_lead=lead)

    templates = (
        EmailTemplate.query.filter_by(is_active=True)
        .order_by(EmailTemplate.name.asc())
        .all()
    )

    if form.validate_on_submit():
        selected_lead = None
        if form.lead_id.data:
            selected_lead = db.session.get(Lead, form.lead_id.data)
        template = None
        if form.template_id.data:
            template = db.session.get(EmailTemplate, form.template_id.data)

        to_email = form.to_email.data.strip()
        if selected_lead and not to_email and selected_lead.email:
            to_email = selected_lead.email

        if selected_lead and not to_email:
            flash("This lead has no email address.", "danger")
        else:
            record = email_service.compose_and_send(
                to_email=to_email,
                subject=form.subject.data,
                body=form.body.data,
                lead=selected_lead,
                template=template,
                to_name=selected_lead.name if selected_lead else None,
            )
            if record.status == "sent":
                flash("Email sent successfully and saved to history.", "success")
            else:
                flash(
                    f"Email saved to history but delivery failed: {record.error_message}",
                    "warning",
                )
            if selected_lead:
                return redirect(url_for("leads.detail", lead_id=selected_lead.id))
            return redirect(url_for("emails.index"))

    return render_template(
        "emails/compose.html",
        title="Compose Email",
        form=form,
        lead=lead,
        templates_json=email_service.template_payload(templates, lead),
        smtp_ready=email_service.smtp_configured(),
        smtp_message=email_service.smtp_status_message(),
        placeholder_help=[
            "name",
            "company",
            "email",
            "phone",
            "country",
            "industry",
            "status",
            "lead_source",
            "company_name",
            "sender_name",
        ],
    )


@emails_bp.route("/api/template-preview")
@login_required
def template_preview():
    """Return rendered template content for the compose UI."""
    template_id = request.args.get("template_id", type=int)
    lead_id = request.args.get("lead_id", type=int)
    template = db.session.get(EmailTemplate, template_id) if template_id else None
    if template is None:
        abort(404)
    lead = db.session.get(Lead, lead_id) if lead_id else None
    context = email_service.lead_context(lead)
    return jsonify(
        {
            "id": template.id,
            "name": template.name,
            "subject": email_service.render_placeholders(template.subject, context),
            "body": email_service.render_placeholders(template.body, context),
        }
    )


@emails_bp.route("/history/<int:message_id>")
@login_required
def detail(message_id: int):
    message = EmailMessage.query.get_or_404(message_id)
    return render_template(
        "emails/detail.html",
        title=message.subject,
        message=message,
    )


@emails_bp.route("/templates")
@login_required
def templates():
    items = EmailTemplate.query.order_by(EmailTemplate.name.asc()).all()
    return render_template(
        "emails/templates.html",
        title="Email Templates",
        templates=items,
    )


@emails_bp.route("/templates/new", methods=["GET", "POST"])
@login_required
def template_create():
    form = EmailTemplateForm()
    if form.validate_on_submit():
        tpl = EmailTemplate(
            name=form.name.data.strip(),
            subject=form.subject.data.strip(),
            body=form.body.data.strip(),
            is_active=bool(form.is_active.data),
            created_by_id=current_user.id,
        )
        db.session.add(tpl)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("A template with that name already exists.", "danger")
        else:
            flash("Email template created.", "success")
            return redirect(url_for("emails.templates"))
    return render_template(
        "emails/template_form.html",
        title="New Email Template",
        form=form,
        template=None,
    )


@emails_bp.route("/templates/<int:template_id>/edit", methods=["GET", "POST"])
@login_required
def template_edit(template_id: int):
    tpl = EmailTemplate.query.get_or_404(template_id)
    form = EmailTemplateForm(obj=tpl)
    if form.validate_on_submit():
        tpl.name = form.name.data.strip()
        tpl.subject = form.subject.data.strip()
        tpl.body = form.body.data.strip()
        tpl.is_active = bool(form.is_active.data)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("A template with that name already exists.", "danger")
        else:
            flash("Email template updated.", "success")
            return redirect(url_for("emails.templates"))
    return render_template(
        "emails/template_form.html",
        title="Edit Email Template",
        form=form,
        template=tpl,
    )


@emails_bp.route("/templates/<int:template_id>/delete", methods=["POST"])
@login_required
def template_delete(template_id: int):
    tpl = EmailTemplate.query.get_or_404(template_id)
    db.session.delete(tpl)
    db.session.commit()
    flash(f"Template “{tpl.name}” deleted.", "info")
    return redirect(url_for("emails.templates"))
