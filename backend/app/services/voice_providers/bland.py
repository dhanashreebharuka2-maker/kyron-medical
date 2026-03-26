"""Bland AI outbound calls (voice handoff)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.config import settings
from app.services.voice_providers.riley_prompts import first_message_for_structured
from app.utils.http_client import async_httpx_client

logger = logging.getLogger(__name__)

BLAND_API_BASE = "https://api.bland.ai"


def bland_fully_configured() -> bool:
    """Only BLAND_API_KEY is required; BLAND_WEBHOOK_URL is optional."""
    api_key = getattr(settings, "bland_api_key", None)
    return bool((api_key or "").strip())


def _bland_webhook_url() -> Optional[str]:
    """Return the resolved webhook URL (with path appended if only origin was set), or None."""
    url = (getattr(settings, "bland_webhook_url", None) or "").strip()
    if not url:
        return None
    if not url.startswith("https://"):
        return None
    if not url.endswith("/api/voice/bland-webhook"):
        url = url.rstrip("/") + "/api/voice/bland-webhook"
    return url


@dataclass
class BlandOutboundResult:
    ok: bool
    demo_mode: bool
    error: Optional[str] = None
    call_id: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


def _auth_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": api_key, "Content-Type": "application/json"}


async def initiate_outbound_handoff(
    customer_e164: str,
    structured_context: Dict[str, Any],
    continuation_prompt: str,
) -> BlandOutboundResult:
    """Place an outbound call via Bland AI."""
    if not bland_fully_configured():
        logger.info("Bland not configured; outbound call skipped (demo handoff).")
        return BlandOutboundResult(ok=True, demo_mode=True)

    api_key = (getattr(settings, "bland_api_key", None) or "").strip()
    _TASK_MAX_CHARS = 14000
    task = (continuation_prompt or "")[:_TASK_MAX_CHARS]
    first_sentence = (first_message_for_structured(structured_context) or "").strip()[:500]
    sid = structured_context.get("session_id")

    selected_slot = structured_context.get("selected_slot") or {}
    body: Dict[str, Any] = {
        "phone_number": customer_e164,
        "task": task,
        "first_sentence": first_sentence,
        "metadata": {
            "kyron_session_id": sid,
            "selected_slot_id": selected_slot.get("id") if isinstance(selected_slot, dict) else None,
        },
    }

    webhook_url = _bland_webhook_url()
    if webhook_url:
        body["webhook"] = webhook_url

    # Optional overrides from env
    bland_voice = getattr(settings, "bland_voice", None)
    bland_model = getattr(settings, "bland_model", None)
    bland_language = getattr(settings, "bland_language", None)
    if (bland_voice or "").strip():
        body["voice"] = bland_voice.strip()
    if (bland_model or "").strip():
        body["model"] = bland_model.strip()
    if (bland_language or "").strip():
        body["language"] = bland_language.strip()

    url = f"{BLAND_API_BASE}/v1/calls"
    try:
        async with async_httpx_client(timeout=45.0) as client:
            r = await client.post(url, headers=_auth_headers(api_key), json=body)

        if r.status_code in (200, 201):
            data = r.json()
            if isinstance(data, dict):
                call_id = data.get("call_id") or data.get("id")
                call_id_s = call_id.strip() if isinstance(call_id, str) else None
                return BlandOutboundResult(ok=True, demo_mode=False, call_id=call_id_s, raw=data)
            return BlandOutboundResult(ok=True, demo_mode=False, raw={"raw": data})

        detail = (r.text or "")[:800]
        if "TLSV1_ALERT_PROTOCOL_VERSION" in detail:
            detail = (
                "TLS version error — your Python/OpenSSL build is too old. "
                "Install Python 3.12 via Homebrew and recreate the venv. " + detail
            )
        return BlandOutboundResult(
            ok=False, demo_mode=False, error=f"Bland API error ({r.status_code}): {detail}"
        )
    except Exception as e:
        err = str(e)[:500]
        if "TLSV1_ALERT_PROTOCOL_VERSION" in err:
            err = (
                "TLS version error — your Python/OpenSSL build is too old. "
                "Install Python 3.12 via Homebrew and recreate the venv."
            )
        return BlandOutboundResult(ok=False, demo_mode=False, error=f"Bland request failed: {err}")


async def fetch_bland_call(call_id: str) -> Optional[Dict[str, Any]]:
    """Fetch call details (transcript) from Bland for post-call finalization."""
    api_key = (getattr(settings, "bland_api_key", None) or "").strip()
    if not api_key:
        return None
    url = f"{BLAND_API_BASE}/v1/calls/{call_id}"
    try:
        async with async_httpx_client(timeout=30.0) as client:
            r = await client.get(url, headers=_auth_headers(api_key))
        if r.status_code == 200:
            return r.json()
        logger.warning("fetch_bland_call status=%s", r.status_code)
        return None
    except Exception as e:
        logger.warning("fetch_bland_call error: %s", e)
        return None
