"""WhatsApp delivery providers.

Current default: Click-to-Chat (wa.me) — opens WhatsApp with a predefined message.
Future: WhatsApp Business API (Meta Cloud API) can be enabled via settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote

from flask import current_app


@dataclass
class ProviderResult:
    """Normalized result from any WhatsApp provider."""

    ok: bool
    status: str  # opened | sent | failed | queued
    provider: str
    external_url: str | None = None
    external_id: str | None = None
    error_message: str | None = None
    raw: dict | None = None


class WhatsAppProvider(Protocol):
    """Extension point for WhatsApp delivery backends."""

    name: str

    def send_text(self, *, to_number: str, message: str) -> ProviderResult:
        """Deliver (or prepare) a text message to a WhatsApp number."""


class ClickToChatProvider:
    """Open WhatsApp Web/App chat with a prefilled message via wa.me."""

    name = "click_to_chat"

    def send_text(self, *, to_number: str, message: str) -> ProviderResult:
        digits = "".join(ch for ch in (to_number or "") if ch.isdigit())
        if not digits:
            return ProviderResult(
                ok=False,
                status="failed",
                provider=self.name,
                error_message="WhatsApp number must contain digits in international format.",
            )
        url = f"https://wa.me/{digits}"
        if message:
            url = f"{url}?text={quote(message)}"
        return ProviderResult(
            ok=True,
            status="opened",
            provider=self.name,
            external_url=url,
            raw={"channel": "wa.me"},
        )


class WhatsAppBusinessAPIProvider:
    """Stub for Meta WhatsApp Business Cloud API.

    Configure AppSettings / env:
      - whatsapp_api_base_url (default https://graph.facebook.com/v19.0)
      - whatsapp_api_token
      - whatsapp_phone_number_id

    When credentials are present, this provider will POST to:
      {base}/{phone_number_id}/messages

    Until credentials are configured, calls fail with a clear setup message so
    Click-to-Chat remains the active path.
    """

    name = "business_api"

    def __init__(
        self,
        *,
        api_token: str | None,
        phone_number_id: str | None,
        api_base_url: str | None = None,
    ) -> None:
        self.api_token = (api_token or "").strip()
        self.phone_number_id = (phone_number_id or "").strip()
        self.api_base_url = (
            (api_base_url or "").strip()
            or "https://graph.facebook.com/v19.0"
        ).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_token and self.phone_number_id)

    def send_text(self, *, to_number: str, message: str) -> ProviderResult:
        digits = "".join(ch for ch in (to_number or "") if ch.isdigit())
        if not digits:
            return ProviderResult(
                ok=False,
                status="failed",
                provider=self.name,
                error_message="WhatsApp number must contain digits in international format.",
            )

        if not self.configured:
            return ProviderResult(
                ok=False,
                status="failed",
                provider=self.name,
                error_message=(
                    "WhatsApp Business API is not configured. "
                    "Set API token and phone number ID, or switch provider to Click-to-Chat."
                ),
            )

        # Future implementation hook — intentionally not calling the network yet
        # so the CRM can ship today while remaining API-ready.
        endpoint = f"{self.api_base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": digits,
            "type": "text",
            "text": {"body": message},
        }
        current_app.logger.info(
            "WhatsApp Business API ready at %s (not sent — implement HTTP client next)",
            endpoint,
        )
        return ProviderResult(
            ok=False,
            status="failed",
            provider=self.name,
            error_message=(
                "WhatsApp Business API provider scaffold is in place, but live HTTP "
                "sending is not enabled yet. Use Click-to-Chat for now, or complete "
                f"the API client against {endpoint}."
            ),
            raw={"endpoint": endpoint, "payload": payload},
        )


def get_provider(settings) -> WhatsAppProvider:
    """Factory: return the configured WhatsApp provider."""
    provider_name = (getattr(settings, "whatsapp_provider", None) or "click_to_chat").strip()
    if provider_name == "business_api":
        return WhatsAppBusinessAPIProvider(
            api_token=getattr(settings, "whatsapp_api_token", None),
            phone_number_id=getattr(settings, "whatsapp_phone_number_id", None),
            api_base_url=getattr(settings, "whatsapp_api_base_url", None),
        )
    return ClickToChatProvider()
