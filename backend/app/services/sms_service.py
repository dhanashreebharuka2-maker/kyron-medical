"""SMS via Textbelt, Twilio, or mock."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import httpx
from zoneinfo import ZoneInfo

from app.config import settings

logger = logging.getLogger(__name__)

TEXTBELT_TEXT_URL = "https://textbelt.com/text"


@dataclass(frozen=True)
class SmsSendResult:
    """Result of attempting to send an SMS."""

    ok: bool
    mock: bool
    error: str | None = None
    twilio_message_sid: str | None = None
    twilio_status: str | None = None
    textbelt_text_id: str | None = None


def _twilio_error_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
        msg = (data.get("message") or "").strip()
        code = data.get("code")
        if code is not None and msg:
            return f"[{code}] {msg}"
        if msg:
            return msg
        return (response.text or f"HTTP {response.status_code}")[:500]
    except Exception:
        return (response.text or f"HTTP {response.status_code}")[:500]


# Mock slots store naive datetimes as office-local wall time (Austin / Central).
_OFFICE_TZ = ZoneInfo("America/Chicago")


def format_booking_time_for_sms(start_iso: str) -> str:
    """Human-readable appointment time for SMS (Central)."""
    dt = datetime.fromisoformat(start_iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_OFFICE_TZ)
    else:
        dt = dt.astimezone(_OFFICE_TZ)
    hour12 = dt.hour % 12 or 12
    am_pm = "AM" if dt.hour < 12 else "PM"
    return f"{dt:%a %b %d}, {hour12}:{dt.minute:02d} {am_pm} CT"


def build_booking_confirmation_sms_body(booking: Dict[str, Any]) -> str:
    """Short, patient-friendly confirmation text (carriers may split long GSM segments)."""
    when = format_booking_time_for_sms(booking["start_iso"])
    prov = booking.get("provider_name") or "your provider"
    office = booking.get("office_name") or "Kyron Medical"
    phone = booking.get("office_phone") or ""
    return (
        f"Kyron Medical: You're confirmed with {prov} on {when}. "
        f"{office}. Call {phone} with questions."
    )


def _us_10_from_e164(e164: str) -> str | None:
    d = re.sub(r"\D", "", e164)
    if len(d) == 11 and d.startswith("1"):
        return d[1:]
    if len(d) == 10:
        return d
    return None


def resolve_active_sms_provider() -> str:
    """
    Which backend will send: textbelt | twilio | none (mock).
    """
    p = (settings.sms_provider or "auto").strip().lower()
    if p == "textbelt":
        return "textbelt" if (settings.textbelt_api_key or "").strip() else "none"
    if p == "twilio":
        return (
            "twilio"
            if (
                settings.twilio_account_sid
                and settings.twilio_auth_token
                and settings.twilio_from_number
            )
            else "none"
        )
    # auto
    if (settings.textbelt_api_key or "").strip():
        return "textbelt"
    if (
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from_number
    ):
        return "twilio"
    return "none"


async def _send_textbelt(to_phone_e164: str, message: str) -> SmsSendResult:
    key = (settings.textbelt_api_key or "").strip()
    if not key:
        logger.info("Textbelt key missing; SMS confirmation simulated for …%s", to_phone_e164[-4:])
        return SmsSendResult(ok=True, mock=True)

    phone = _us_10_from_e164(to_phone_e164)
    if not phone:
        return SmsSendResult(
            ok=False,
            mock=False,
            error="Textbelt supports US numbers only; use a +1 ten-digit mobile.",
        )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                TEXTBELT_TEXT_URL,
                data={"phone": phone, "message": message, "key": key},
            )
        try:
            data = r.json()
        except Exception:
            return SmsSendResult(
                ok=False,
                mock=False,
                error=(r.text or f"HTTP {r.status_code}")[:300],
            )

        if data.get("success"):
            tid = data.get("textId")
            tid_str = str(tid) if tid is not None else None
            logger.info("Textbelt SMS accepted textId=%s to=…%s", tid_str, to_phone_e164[-4:])
            return SmsSendResult(ok=True, mock=False, textbelt_text_id=tid_str)

        err = (data.get("error") or "Textbelt send failed")[:300]
        logger.warning("Textbelt SMS failed To=…%s %s", to_phone_e164[-4:], err)
        return SmsSendResult(ok=False, mock=False, error=err)
    except Exception as e:
        logger.exception("Textbelt SMS request failed")
        return SmsSendResult(ok=False, mock=False, error=str(e)[:300])


async def _send_twilio(to_phone_e164: str, message: str) -> SmsSendResult:
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.twilio_account_sid}/Messages.json"
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data={
                    "To": to_phone_e164,
                    "From": settings.twilio_from_number,
                    "Body": message,
                },
            )
        if r.status_code not in (200, 201):
            detail = _twilio_error_detail(r)
            logger.warning("Twilio SMS failed To=…%s status=%s %s", to_phone_e164[-4:], r.status_code, detail)
            return SmsSendResult(ok=False, mock=False, error=detail)

        try:
            data = r.json()
        except Exception:
            data = {}
        sid = data.get("sid")
        st = (data.get("status") or "").lower()
        err_code = data.get("error_code")
        err_msg = (data.get("error_message") or "").strip()
        if err_code or err_msg or st in ("failed", "undelivered"):
            detail = f"[{err_code}] {err_msg or st}".strip() if (err_code or err_msg or st) else "Twilio rejected message"
            logger.warning("Twilio SMS body error To=…%s %s", to_phone_e164[-4:], detail)
            return SmsSendResult(ok=False, mock=False, error=detail)

        logger.info(
            "Twilio SMS accepted sid=%s status=%s to=…%s",
            sid,
            st or "?",
            to_phone_e164[-4:],
        )
        return SmsSendResult(ok=True, mock=False, twilio_message_sid=sid, twilio_status=st or None)
    except Exception as e:
        logger.exception("Twilio SMS request failed")
        return SmsSendResult(ok=False, mock=False, error=str(e)[:300])


async def send_sms_confirmation(to_phone_e164: str, message: str) -> SmsSendResult:
    """Send via Textbelt or Twilio when configured; otherwise simulate success (mock)."""
    provider = resolve_active_sms_provider()
    if provider == "textbelt":
        return await _send_textbelt(to_phone_e164, message)
    if provider == "twilio":
        return await _send_twilio(to_phone_e164, message)
    logger.info("SMS not configured (no Textbelt key / Twilio); simulated for …%s", to_phone_e164[-4:])
    return SmsSendResult(ok=True, mock=True)


def sms_delivery_ref(res: SmsSendResult) -> str | None:
    """Single reference id for session storage / UI (Twilio SID or Textbelt textId)."""
    return res.twilio_message_sid or res.textbelt_text_id


def to_e164_us(digits_10: str) -> str:
    return f"+1{digits_10}"
