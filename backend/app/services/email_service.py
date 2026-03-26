"""Booking confirmation email — Resend API or mock."""
from __future__ import annotations


import logging
import httpx

from app.config import settings
from app.data.office import OFFICE

logger = logging.getLogger(__name__)


async def send_booking_confirmation_email(
    to_email: str,
    patient_name: str,
    provider_name: str,
    specialty: str,
    start_iso: str,
) -> tuple[bool, bool]:
    """
    Returns (success, is_mock).
    """
    body = f"""
Kyron Medical — Appointment Confirmation

Patient: {patient_name}
Provider: {provider_name}
Specialty: {specialty}
Date & time: {start_iso}

Location:
{OFFICE['name']}
{OFFICE['address_line1']}, {OFFICE['address_line2']}
{OFFICE['city']}, {OFFICE['state']} {OFFICE['zip']}

Phone: {OFFICE['phone']}

This message is for scheduling confirmation only and does not constitute medical advice.
""".strip()

    if not settings.resend_api_key:
        logger.info(
            "BOOKING EMAIL (demo — not sent; set RESEND_API_KEY to use Resend):\n%s",
            body[:2000],
        )
        return True, True

    if not to_email or not to_email.strip():
        logger.info("BOOKING EMAIL skipped: no patient email on session.\n%s", body[:2000])
        return True, True

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.email_from,
                    "to": [to_email],
                    "subject": "Your Kyron Medical appointment confirmation",
                    "text": body,
                },
            )
        if r.status_code not in (200, 201):
            logger.warning(
                "Resend booking email failed status=%s body=%s to=%s from=%s",
                r.status_code,
                (r.text or "")[:500],
                to_email,
                settings.email_from,
            )
        return r.status_code in (200, 201), False
    except Exception:
        logger.exception("Resend booking email request failed to=%s", to_email)
        return False, False
