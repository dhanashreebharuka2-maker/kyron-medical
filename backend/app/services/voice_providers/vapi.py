"""Vapi outbound calls (voice handoff)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.config import settings
from app.services.voice_providers.alex_prompts import first_message_for_structured
from app.utils.http_client import async_httpx_client

logger = logging.getLogger(__name__)

VAPI_API_BASE_DEFAULT = "https://api.vapi.ai"


def vapi_fully_configured() -> bool:
    key = (settings.vapi_api_key or "").strip()
    assistant_id = (settings.vapi_assistant_id or "").strip()
    phone_id = (settings.vapi_phone_number_id or "").strip()
    # Webhook URL is configured on the assistant in the Vapi dashboard (not on POST /call — API rejects serverUrl).
    return bool(key and assistant_id and phone_id)


@dataclass
class VapiOutboundResult:
    ok: bool
    demo_mode: bool
    error: Optional[str] = None
    call_id: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


def _auth_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


async def initiate_vapi_handoff(
    customer_e164: str,
    structured_context: Dict[str, Any],
    continuation_prompt: str,
) -> VapiOutboundResult:
    """
    Create an outbound call via Vapi.

    Vapi's API has had a few endpoint shapes across versions; we try the common ones.
    """
    if not vapi_fully_configured():
        logger.info("Vapi not configured; outbound call skipped (demo handoff).")
        return VapiOutboundResult(ok=True, demo_mode=True)

    api_key = (settings.vapi_api_key or "").strip()
    assistant_id = (settings.vapi_assistant_id or "").strip()
    phone_id = (settings.vapi_phone_number_id or "").strip()

    # Session instructions go in variableValues.kyron_context; the Vapi assistant should reference {{kyron_context}}.
    # kyron_session_id is for custom tools (e.g. kyron_sms_opt_in → POST /api/notify/sms-opt-in).
    # Vapi variableValues must stay within a reasonable size; 8k was truncating slot lists + tail context.
    _KYRON_CONTEXT_MAX_CHARS = 14000
    task = (continuation_prompt or "")[:_KYRON_CONTEXT_MAX_CHARS]
    first_msg = (first_message_for_structured(structured_context) or "").strip()[:500]
    sid = structured_context.get("session_id")
    sid_str = str(sid).strip() if sid is not None else ""

    body: Dict[str, Any] = {
        "assistantId": assistant_id,
        "phoneNumberId": phone_id,
        "customer": {"number": customer_e164},
        "metadata": {
            "kyron_session_id": sid,
            "selected_slot_id": ((structured_context.get("selected_slot") or {}) or {}).get("id"),
        },
        # assistantOverrides.model requires provider + full model config — Vapi returns 400 if only
        # messages is sent.  Use variableValues only; the Vapi dashboard assistant system prompt
        # must contain {{kyron_context}} so the variable is interpolated into the model context.
        "assistantOverrides": {
            "firstMessage": first_msg,
            "variableValues": {
                "kyron_context": task,
                "kyron_session_id": sid_str,
            },
        },
    }

    # Endpoints to try (first success wins).
    bases = [VAPI_API_BASE_DEFAULT]
    endpoints = [
        "/call",  # common
        "/calls",  # variant
        "/call/phone",  # older variant
    ]

    last_err: Optional[str] = None
    for base in bases:
        for ep in endpoints:
            url = base.rstrip("/") + ep
            try:
                async with async_httpx_client(timeout=45.0) as client:
                    r = await client.post(url, headers=_auth_headers(api_key), json=body)
                if r.status_code in (200, 201):
                    data = r.json()
                    if isinstance(data, dict):
                        call_id = (
                            data.get("id")
                            or data.get("callId")
                            or data.get("call_id")
                            or (data.get("call") or {}).get("id")
                        )
                        call_id_s = call_id.strip() if isinstance(call_id, str) else None
                        return VapiOutboundResult(ok=True, demo_mode=False, call_id=call_id_s, raw=data)
                    return VapiOutboundResult(ok=True, demo_mode=False, raw={"raw": data})

                # Try next endpoint only on "not found" style errors.
                if r.status_code in (404, 405):
                    last_err = f"{r.status_code} at {ep}"
                    continue

                detail = (r.text or "")[:800]
                return VapiOutboundResult(ok=False, demo_mode=False, error=f"Vapi API error ({r.status_code}): {detail}")
            except Exception as e:
                last_err = str(e)[:500]
                continue

    return VapiOutboundResult(ok=False, demo_mode=False, error=f"Vapi request failed: {last_err or 'unknown error'}")

