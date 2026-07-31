"""WhatsApp templates, history, and send orchestration."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from flask_login import current_user

from app.extensions import db
from app.models import Customer, Lead, WhatsAppMessage, WhatsAppTemplate
from app.services.activity import log_activity
from app.services.settings_service import get_settings
from app.services.whatsapp_providers import ProviderResult, get_provider

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

DEFAULT_TEMPLATES = (
    {
        "name": "Quick Hello",
        "body": (
            "Hi {{name}}, this is {{sender_name}} from {{company_name}}. "
            "Just wanted to connect on WhatsApp."
        ),
    },
    {
        "name": "Follow-up",
        "body": (
            "Hi {{name}}, following up regarding {{company}}. "
            "Do you have a few minutes to chat?"
        ),
    },
    {
        "name": "Meeting Reminder",
        "body": (
            "Hi {{name}}, reminding you about our upcoming discussion for {{company}}. "
            "Please reply here if you need to reschedule. — {{sender_name}}"
        ),
    },
)

WHATSAPP_PROVIDERS = (
    ("click_to_chat", "Click-to-Chat (wa.me)"),
    ("business_api", "WhatsApp Business API (future)"),
)


def normalize_whatsapp_number(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    # Keep leading + for display, digits for dialing
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if not digits:
        return None
    if cleaned.startswith("+"):
        return f"+{digits}"
    return digits


def digits_only(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def resolve_whatsapp_number(
    *,
    lead: Lead | None = None,
    customer: Customer | None = None,
    explicit: str | None = None,
) -> str | None:
    if explicit:
        return normalize_whatsapp_number(explicit)
    if lead and lead.whatsapp_number:
        return normalize_whatsapp_number(lead.whatsapp_number)
    if lead and lead.phone:
        return normalize_whatsapp_number(lead.phone)
    if customer and customer.whatsapp_number:
        return normalize_whatsapp_number(customer.whatsapp_number)
    if customer and customer.phone:
        return normalize_whatsapp_number(customer.phone)
    return None


def contact_context(
    *,
    lead: Lead | None = None,
    customer: Customer | None = None,
    sender_name: str | None = None,
) -> dict[str, str]:
    settings = get_settings()
    name = ""
    company = ""
    if lead:
        name = lead.name or ""
        company = lead.company or ""
    elif customer:
        name = customer.primary_contact or customer.name or ""
        company = customer.name or ""
    return {
        "name": name,
        "company": company,
        "company_name": settings.company_name or "Mini CRM",
        "sender_name": sender_name
        or (current_user.full_name if current_user.is_authenticated else "Mini CRM"),
        "phone": (lead.phone if lead else (customer.phone if customer else "")) or "",
        "whatsapp_number": resolve_whatsapp_number(lead=lead, customer=customer) or "",
    }


def render_placeholders(text: str, context: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        return str(context.get(match.group(1), match.group(0)))

    return PLACEHOLDER_RE.sub(repl, text or "")


def provider_status_message(settings=None) -> str:
    settings = settings or get_settings()
    provider = (settings.whatsapp_provider or "click_to_chat").strip()
    if provider == "business_api":
        if settings.whatsapp_api_token and settings.whatsapp_phone_number_id:
            return "WhatsApp Business API selected (scaffold ready — complete HTTP client to go live)."
        return "WhatsApp Business API selected but credentials are missing."
    return "Click-to-Chat enabled — messages open in WhatsApp with a prefilled text."


def compose_and_dispatch(
    *,
    message_body: str,
    to_number: str | None = None,
    lead: Lead | None = None,
    customer: Customer | None = None,
    template: WhatsAppTemplate | None = None,
    user_id: int | None = None,
    open_chat: bool = True,
) -> tuple[WhatsAppMessage, ProviderResult]:
    """Render message, call the active provider, and store history."""
    settings = get_settings()
    uid = user_id or current_user.id
    number = resolve_whatsapp_number(lead=lead, customer=customer, explicit=to_number)
    context = contact_context(lead=lead, customer=customer)
    rendered = render_placeholders(message_body, context).strip()

    record = WhatsAppMessage(
        to_number=number or "",
        message_body=rendered,
        status="queued",
        provider=settings.whatsapp_provider or "click_to_chat",
        lead_id=lead.id if lead else None,
        customer_id=customer.id if customer else None,
        template_id=template.id if template else None,
        sent_by_id=uid,
    )
    db.session.add(record)
    db.session.flush()

    if not number:
        result = ProviderResult(
            ok=False,
            status="failed",
            provider=record.provider,
            error_message="No WhatsApp number available for this contact.",
        )
    else:
        provider = get_provider(settings)
        result = provider.send_text(to_number=number, message=rendered if open_chat else "")

    record.status = result.status
    record.provider = result.provider
    record.external_url = result.external_url
    record.external_id = result.external_id
    record.error_message = result.error_message
    if result.ok:
        record.sent_at = datetime.now(timezone.utc)

    entity_type = "lead" if lead else ("customer" if customer else "whatsapp")
    entity_id = lead.id if lead else (customer.id if customer else record.id)
    action = "whatsapp_opened" if result.status == "opened" else (
        "whatsapp_sent" if result.status == "sent" else "whatsapp_failed"
    )
    log_activity(
        action,
        f"WhatsApp to {record.to_number or 'unknown'}: {rendered[:80]}",
        lead_id=lead.id if lead else None,
        customer_id=customer.id if customer else None,
        entity_type=entity_type,
        entity_id=entity_id,
        details=f"message_id={record.id}; provider={record.provider}; status={record.status}",
        user_id=uid,
    )
    db.session.commit()
    return record, result


def seed_default_templates(user_id: int | None = None) -> int:
    if WhatsAppTemplate.query.count():
        return 0
    created = 0
    for item in DEFAULT_TEMPLATES:
        db.session.add(
            WhatsAppTemplate(
                name=item["name"],
                body=item["body"],
                is_active=True,
                created_by_id=user_id,
            )
        )
        created += 1
    if created:
        db.session.commit()
    return created


def template_payload(
    templates: list[WhatsAppTemplate],
    *,
    lead: Lead | None = None,
    customer: Customer | None = None,
) -> list[dict]:
    context = contact_context(lead=lead, customer=customer)
    return [
        {
            "id": tpl.id,
            "name": tpl.name,
            "body": tpl.body,
            "rendered_body": render_placeholders(tpl.body, context),
        }
        for tpl in templates
    ]
