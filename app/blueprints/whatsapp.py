"""WhatsApp integration — click-to-chat, templates, history, API-ready settings."""

from __future__ import annotations

from flask import (
    Blueprint,
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

from app.decorators import admin_required
from app.extensions import db
from app.forms import ComposeWhatsAppForm, WhatsAppSettingsForm, WhatsAppTemplateForm
from app.models import Customer, Lead, WhatsAppMessage, WhatsAppTemplate
from app.services import whatsapp_service
from app.services.settings_service import get_settings

whatsapp_bp = Blueprint("whatsapp", __name__, url_prefix="/whatsapp")


def _populate_compose_form(
    form: ComposeWhatsAppForm,
    *,
    lead: Lead | None = None,
    customer: Customer | None = None,
) -> None:
    leads = Lead.query.order_by(Lead.name.asc()).all()
    customers = Customer.query.order_by(Customer.name.asc()).all()
    form.lead_id.choices = [(0, "— Select lead —")] + [
        (
            item.id,
            f"{item.name}"
            + (
                f" ({item.effective_whatsapp})"
                if item.effective_whatsapp
                else " (no WhatsApp)"
            ),
        )
        for item in leads
    ]
    form.customer_id.choices = [(0, "— Select customer —")] + [
        (
            item.id,
            f"{item.name}"
            + (
                f" ({item.effective_whatsapp})"
                if item.effective_whatsapp
                else " (no WhatsApp)"
            ),
        )
        for item in customers
    ]
    templates = (
        WhatsAppTemplate.query.filter_by(is_active=True)
        .order_by(WhatsAppTemplate.name.asc())
        .all()
    )
    form.template_id.choices = [(0, "— Custom message —")] + [
        (tpl.id, tpl.name) for tpl in templates
    ]

    if request.method == "GET":
        if lead:
            form.lead_id.data = lead.id
            form.to_number.data = lead.effective_whatsapp or ""
        if customer:
            form.customer_id.data = customer.id
            if not form.to_number.data:
                form.to_number.data = customer.effective_whatsapp or ""


@whatsapp_bp.route("/")
@login_required
def index():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = WhatsAppMessage.query
    if status in {"opened", "sent", "failed", "queued"}:
        query = query.filter(WhatsAppMessage.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                WhatsAppMessage.to_number.ilike(like),
                WhatsAppMessage.message_body.ilike(like),
            )
        )

    pagination = query.order_by(WhatsAppMessage.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "whatsapp/history.html",
        title="WhatsApp History",
        messages=pagination.items,
        pagination=pagination,
        q=q,
        status=status,
        provider_message=whatsapp_service.provider_status_message(),
    )


@whatsapp_bp.route("/compose", methods=["GET", "POST"])
@login_required
def compose():
    lead_id = request.args.get("lead_id", type=int) or request.form.get("lead_id", type=int)
    customer_id = request.args.get("customer_id", type=int) or request.form.get(
        "customer_id", type=int
    )
    lead = db.session.get(Lead, lead_id) if lead_id else None
    customer = db.session.get(Customer, customer_id) if customer_id else None

    form = ComposeWhatsAppForm()
    _populate_compose_form(form, lead=lead, customer=customer)
    templates = (
        WhatsAppTemplate.query.filter_by(is_active=True)
        .order_by(WhatsAppTemplate.name.asc())
        .all()
    )

    if form.validate_on_submit():
        selected_lead = db.session.get(Lead, form.lead_id.data) if form.lead_id.data else None
        selected_customer = (
            db.session.get(Customer, form.customer_id.data) if form.customer_id.data else None
        )
        template = (
            db.session.get(WhatsAppTemplate, form.template_id.data)
            if form.template_id.data
            else None
        )
        record, result = whatsapp_service.compose_and_dispatch(
            message_body=form.message_body.data,
            to_number=form.to_number.data,
            lead=selected_lead,
            customer=selected_customer,
            template=template,
        )
        if result.ok and result.external_url:
            flash("WhatsApp chat prepared and saved to history.", "success")
            return redirect(result.external_url)
        if result.ok:
            flash("WhatsApp message recorded.", "success")
        else:
            flash(
                f"WhatsApp action saved to history but failed: {result.error_message}",
                "warning",
            )
        if selected_lead:
            return redirect(url_for("leads.detail", lead_id=selected_lead.id))
        if selected_customer:
            return redirect(url_for("customers.detail", customer_id=selected_customer.id))
        return redirect(url_for("whatsapp.index"))

    return render_template(
        "whatsapp/compose.html",
        title="WhatsApp Compose",
        form=form,
        lead=lead,
        customer=customer,
        templates_json=whatsapp_service.template_payload(
            templates, lead=lead, customer=customer
        ),
        provider_message=whatsapp_service.provider_status_message(),
        placeholder_help=["name", "company", "company_name", "sender_name", "phone", "whatsapp_number"],
    )


@whatsapp_bp.route("/api/template-preview")
@login_required
def template_preview():
    template_id = request.args.get("template_id", type=int)
    lead_id = request.args.get("lead_id", type=int)
    customer_id = request.args.get("customer_id", type=int)
    template = db.session.get(WhatsAppTemplate, template_id) if template_id else None
    if template is None:
        return jsonify({"error": "not found"}), 404
    lead = db.session.get(Lead, lead_id) if lead_id else None
    customer = db.session.get(Customer, customer_id) if customer_id else None
    context = whatsapp_service.contact_context(lead=lead, customer=customer)
    return jsonify(
        {
            "id": template.id,
            "name": template.name,
            "body": whatsapp_service.render_placeholders(template.body, context),
        }
    )


@whatsapp_bp.route("/history/<int:message_id>")
@login_required
def detail(message_id: int):
    message = WhatsAppMessage.query.get_or_404(message_id)
    return render_template(
        "whatsapp/detail.html",
        title="WhatsApp Message",
        message=message,
    )


@whatsapp_bp.route("/templates")
@login_required
def templates():
    items = WhatsAppTemplate.query.order_by(WhatsAppTemplate.name.asc()).all()
    return render_template(
        "whatsapp/templates.html",
        title="WhatsApp Templates",
        templates=items,
    )


@whatsapp_bp.route("/templates/new", methods=["GET", "POST"])
@login_required
def template_create():
    form = WhatsAppTemplateForm()
    if form.validate_on_submit():
        tpl = WhatsAppTemplate(
            name=form.name.data.strip(),
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
            flash("WhatsApp template created.", "success")
            return redirect(url_for("whatsapp.templates"))
    return render_template(
        "whatsapp/template_form.html",
        title="New WhatsApp Template",
        form=form,
    )


@whatsapp_bp.route("/templates/<int:template_id>/edit", methods=["GET", "POST"])
@login_required
def template_edit(template_id: int):
    tpl = WhatsAppTemplate.query.get_or_404(template_id)
    form = WhatsAppTemplateForm(obj=tpl)
    if form.validate_on_submit():
        tpl.name = form.name.data.strip()
        tpl.body = form.body.data.strip()
        tpl.is_active = bool(form.is_active.data)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("A template with that name already exists.", "danger")
        else:
            flash("WhatsApp template updated.", "success")
            return redirect(url_for("whatsapp.templates"))
    return render_template(
        "whatsapp/template_form.html",
        title="Edit WhatsApp Template",
        form=form,
    )


@whatsapp_bp.route("/templates/<int:template_id>/delete", methods=["POST"])
@login_required
def template_delete(template_id: int):
    tpl = WhatsAppTemplate.query.get_or_404(template_id)
    name = tpl.name
    db.session.delete(tpl)
    db.session.commit()
    flash(f"Template “{name}” deleted.", "info")
    return redirect(url_for("whatsapp.templates"))


@whatsapp_bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    app_settings = get_settings()
    form = WhatsAppSettingsForm(obj=app_settings)
    if form.validate_on_submit():
        app_settings.whatsapp_provider = form.whatsapp_provider.data
        app_settings.whatsapp_api_base_url = (
            form.whatsapp_api_base_url.data.strip()
            if form.whatsapp_api_base_url.data
            else "https://graph.facebook.com/v19.0"
        )
        if form.whatsapp_api_token.data:
            app_settings.whatsapp_api_token = form.whatsapp_api_token.data.strip()
        app_settings.whatsapp_phone_number_id = (
            form.whatsapp_phone_number_id.data.strip()
            if form.whatsapp_phone_number_id.data
            else None
        )
        app_settings.whatsapp_business_account_id = (
            form.whatsapp_business_account_id.data.strip()
            if form.whatsapp_business_account_id.data
            else None
        )
        db.session.commit()
        flash("WhatsApp settings saved.", "success")
        return redirect(url_for("whatsapp.settings"))

    return render_template(
        "whatsapp/settings.html",
        title="WhatsApp Settings",
        form=form,
        provider_message=whatsapp_service.provider_status_message(app_settings),
    )
