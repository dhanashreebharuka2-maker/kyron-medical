from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.notifications import EmailRequest, SmsOptInRequest, SmsSendResponse
from app.services.email_service import send_booking_confirmation_email
from app.services.session_service import get_session, replace_session
from app.services.sms_service import (
    build_booking_confirmation_sms_body,
    send_sms_confirmation,
    sms_delivery_ref,
    to_e164_us,
)
from app.utils.validation import normalize_phone

router = APIRouter(prefix="/api", tags=["notifications"])


async def apply_sms_opt_in(body: SmsOptInRequest) -> SmsSendResponse:
    """Shared by /api/notify/sms-opt-in and /api/voice/sms-opt-in (Vapi HTTP tool)."""
    s = get_session(body.session_id)
    if not s:
        raise HTTPException(404, "session not found")
    s["sms_opt_in"] = body.opt_in

    if not body.opt_in:
        s["sms_sent"] = False
        s["sms_mock"] = False
        s["sms_last_error"] = None
        s["sms_message_sid"] = None
        replace_session(body.session_id, s)
        out = get_session(body.session_id) or s
        return SmsSendResponse(success=True, message="SMS notifications declined.", mock=True, session=out)

    b = s.get("booking")
    p = s.get("patient") or {}
    digits = normalize_phone(p.get("phone") or "")
    if not digits:
        s["sms_sent"] = False
        s["sms_mock"] = False
        s["sms_message_sid"] = None
        s["sms_last_error"] = "Add a valid 10-digit US phone in intake to receive SMS."
        replace_session(body.session_id, s)
        out = get_session(body.session_id) or s
        return SmsSendResponse(
            success=False,
            message="Need a valid phone on file to send SMS.",
            mock=True,
            session=out,
        )

    # Phone OK but no booking yet — save opt-in; SMS sends when booking is confirmed (web or voice webhook).
    if not b:
        s["sms_sent"] = False
        s["sms_mock"] = False
        s["sms_message_sid"] = None
        s["sms_last_error"] = None
        replace_session(body.session_id, s)
        out = get_session(body.session_id) or s
        return SmsSendResponse(
            success=True,
            message="SMS opt-in saved. Confirmation text sends when your appointment is booked.",
            mock=True,
            session=out,
        )

    sms_res = await send_sms_confirmation(
        to_phone_e164=to_e164_us(digits),
        message=build_booking_confirmation_sms_body(b),
    )
    s["sms_sent"] = sms_res.ok
    s["sms_mock"] = sms_res.mock
    s["sms_last_error"] = sms_res.error if not sms_res.ok else None
    s["sms_message_sid"] = sms_delivery_ref(sms_res) if sms_res.ok and not sms_res.mock else None
    replace_session(body.session_id, s)
    out = get_session(body.session_id) or s
    if sms_res.ok and not sms_res.mock:
        ref = sms_delivery_ref(sms_res)
        msg = (
            f"Confirmation SMS sent (ref {ref}). Check your phone; use Textbelt or Twilio dashboard if needed."
            if ref
            else "Confirmation SMS sent. Check your phone."
        )
    elif sms_res.ok and sms_res.mock:
        msg = "Demo mode: set TEXTBELT_API_KEY or Twilio in backend/.env to send real SMS."
    else:
        msg = sms_res.error or "SMS send failed."
    return SmsSendResponse(success=sms_res.ok, message=msg, mock=sms_res.mock, session=out)


@router.post("/notify/email", response_model=dict)
async def resend_email(body: EmailRequest):
    s = get_session(body.session_id)
    if not s:
        raise HTTPException(404, "session not found")
    b = s.get("booking")
    if not b:
        raise HTTPException(400, "no booking on session")
    p = s["patient"]
    name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or "Patient"
    ok, _mock = await send_booking_confirmation_email(
        p.get("email") or "",
        name,
        b["provider_name"],
        b["specialty"],
        b["start_iso"],
    )
    s["email_sent"] = ok
    replace_session(body.session_id, s)
    return {"success": ok}


@router.post("/notify/sms-opt-in", response_model=SmsSendResponse)
async def sms_opt_in(body: SmsOptInRequest):
    return await apply_sms_opt_in(body)
