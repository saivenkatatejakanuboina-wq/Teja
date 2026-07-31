"""SMTP sending, template rendering, and email history helpers."""

from __future__ import annotations

import re
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage as MimeEmailMessage

from flask import current_app
from flask_login import current_user

from app.extensions import db
from app.models import EmailMessage, EmailTemplate, Lead
from app.services.activity import log_activity
from app.services.settings_service import get_settings

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

DEFAULT_TEMPLATES = (
    {
        "name": "Introduction",
        "subject": "Nice to connect, {{name}}",
        "body": (
            "Hi {{name}},\n\n"
            "Thank you for your interest in {{company_name}}. "
            "I'd love to learn more about {{company}} and how we can help.\n\n"
            "Would you be open to a short call this week?\n\n"
            "Best regards,\n"
            "{{sender_name}}"
        ),
    },
    {
        "name": "Follow-up",
        "subject": "Following up — {{company}}",
        "body": (
            "Hi {{name}},\n\n"
            "Just checking in regarding our earlier conversation about {{company}}. "
            "Happy to answer any questions or share a quick product overview.\n\n"
            "Looking forward to hearing from you.\n\n"
            "Best,\n"
            "{{sender_name}}"
        ),
    },
    {
        "name": "Meeting Invite",
        "subject": "Meeting invitation for {{name}}",
        "body": (
            "Hi {{name}},\n\n"
            "I'd like to schedule a meeting to discuss next steps for {{company}}.\n\n"
            "Please reply with a couple of times that work for you.\n\n"
            "Thanks,\n"
            "{{sender_name}}\n"
            "{{company_name}}"
        ),
    },
)


def lead_context(lead: Lead | None, sender_name: str | None = None) -> dict[str, str]:
    settings = get_settings()
    return {
        "name": (lead.name if lead else "") or "",
        "company": (lead.company if lead else "") or "",
        "email": (lead.email if lead else "") or "",
        "phone": (lead.phone if lead else "") or "",
        "country": (lead.country if lead else "") or "",
        "industry": (lead.industry if lead else "") or "",
        "status": (lead.status if lead else "") or "",
        "lead_source": (lead.lead_source if lead else "") or "",
        "company_name": settings.company_name or "Mini CRM",
        "sender_name": sender_name
        or (current_user.full_name if current_user.is_authenticated else "Mini CRM"),
    }


def render_placeholders(text: str, context: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(context.get(key, match.group(0)))

    return PLACEHOLDER_RE.sub(repl, text or "")


def smtp_configured(settings=None) -> bool:
    settings = settings or get_settings()
    return bool(settings.smtp_host and settings.smtp_from_email)


def smtp_status_message(settings=None) -> str:
    settings = settings or get_settings()
    if smtp_configured(settings):
        return f"SMTP ready ({settings.smtp_host}:{settings.smtp_port or 587})"
    return "SMTP is not configured. Set host and from-email under Settings → SMTP."


def _deliver(
    *,
    to_email: str,
    to_name: str | None,
    subject: str,
    body: str,
    from_email: str,
) -> tuple[bool, str | None]:
    """Send via SMTP. Returns (ok, error_message)."""
    settings = get_settings()

    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        current_app.logger.info(
            "MAIL_SUPPRESS_SEND active — skipping SMTP delivery to %s", to_email
        )
        return True, None

    if not smtp_configured(settings):
        return False, smtp_status_message(settings)

    message = MimeEmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    if to_name:
        message["To"] = f"{to_name} <{to_email}>"
    else:
        message["To"] = to_email
    message.set_content(body)

    host = settings.smtp_host
    port = settings.smtp_port or 587
    username = settings.smtp_username or None
    password = settings.smtp_password or None
    use_tls = bool(settings.smtp_use_tls)

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            if username:
                smtp.login(username, password or "")
            smtp.send_message(message)
        return True, None
    except Exception as exc:  # noqa: BLE001
        current_app.logger.exception("SMTP send failed")
        return False, str(exc)


def compose_and_send(
    *,
    to_email: str,
    subject: str,
    body: str,
    lead: Lead | None = None,
    template: EmailTemplate | None = None,
    to_name: str | None = None,
    user_id: int | None = None,
) -> EmailMessage:
    """Render placeholders, attempt SMTP delivery, and persist email history."""
    settings = get_settings()
    uid = user_id or current_user.id
    sender_name = current_user.full_name if current_user.is_authenticated else "Mini CRM"
    context = lead_context(lead, sender_name=sender_name)

    rendered_subject = render_placeholders(subject, context).strip()
    rendered_body = render_placeholders(body, context).strip()
    from_email = (settings.smtp_from_email or current_user.email or "").strip()
    recipient_name = to_name or (lead.name if lead else None)

    record = EmailMessage(
        to_email=to_email.strip(),
        to_name=recipient_name,
        from_email=from_email or None,
        subject=rendered_subject,
        body=rendered_body,
        status="queued",
        lead_id=lead.id if lead else None,
        template_id=template.id if template else None,
        sent_by_id=uid,
    )
    db.session.add(record)
    db.session.flush()

    ok, error = _deliver(
        to_email=record.to_email,
        to_name=record.to_name,
        subject=record.subject,
        body=record.body,
        from_email=from_email or "noreply@localhost",
    )

    if ok:
        record.status = "sent"
        record.sent_at = datetime.now(timezone.utc)
        record.error_message = None
        log_activity(
            "email_sent",
            f"Sent email “{record.subject}” to {record.to_email}",
            lead_id=lead.id if lead else None,
            entity_type="lead" if lead else "email",
            entity_id=lead.id if lead else record.id,
            details=f"email_id={record.id}",
            user_id=uid,
        )
    else:
        record.status = "failed"
        record.error_message = error
        log_activity(
            "email_failed",
            f"Failed to send email “{record.subject}” to {record.to_email}",
            lead_id=lead.id if lead else None,
            entity_type="lead" if lead else "email",
            entity_id=lead.id if lead else record.id,
            details=error,
            user_id=uid,
        )

    db.session.commit()
    return record


def seed_default_templates(user_id: int | None = None) -> int:
    """Create starter templates if the table is empty."""
    if EmailTemplate.query.count():
        return 0
    created = 0
    for item in DEFAULT_TEMPLATES:
        db.session.add(
            EmailTemplate(
                name=item["name"],
                subject=item["subject"],
                body=item["body"],
                is_active=True,
                created_by_id=user_id,
            )
        )
        created += 1
    if created:
        db.session.commit()
    return created


def template_payload(templates: list[EmailTemplate], lead: Lead | None = None) -> list[dict]:
    """JSON-serializable templates with placeholders rendered for a lead."""
    context = lead_context(lead)
    payload = []
    for tpl in templates:
        payload.append(
            {
                "id": tpl.id,
                "name": tpl.name,
                "subject": tpl.subject,
                "body": tpl.body,
                "rendered_subject": render_placeholders(tpl.subject, context),
                "rendered_body": render_placeholders(tpl.body, context),
            }
        )
    return payload
