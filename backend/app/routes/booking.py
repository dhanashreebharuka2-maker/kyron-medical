from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.booking import BookingRequest, BookingResponse
from app.services.booking_service import create_booking
from app.services.email_service import send_booking_confirmation_email
from app.services.session_logic import recompute_derived
from app.services.session_service import get_session, replace_session
from app.services.sms_service import (
    build_booking_confirmation_sms_body,
    send_sms_confirmation,
    sms_delivery_ref,
    to_e164_us,
)
from app.utils.validation import normalize_phone

router = APIRouter(prefix="/api", tags=["booking"])


@router.post("/book", response_model=BookingResponse)
async def book_appointment(body: BookingRequest):
    s = get_session(body.session_id)
    if not s:
        raise HTTPException(404, "session not found")

    ok, err, booking = create_booking(s, body.slot_id)
    if not ok or not booking:
        return BookingResponse(success=False, message=err, booking=None, session=s)

    s["booking"] = booking
    s["booking_confirmed"] = True
    s["selected_slot_id"] = body.slot_id
    recompute_derived(s)
    replace_session(body.session_id, s)

    p = s["patient"]
    name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or "Patient"
    email_ok, email_mock = await send_booking_confirmation_email(
        p.get("email") or "",
        name,
        booking["provider_name"],
        booking["specialty"],
        booking["start_iso"],
    )
    s["email_sent"] = email_ok
    s["email_mock"] = email_mock
    replace_session(body.session_id, s)

    if email_mock:
        confirm_msg = (
            "Your appointment is confirmed. "
            "(Demo: no real email was sent — add RESEND_API_KEY to backend/.env and a verified sender domain to send mail.)"
        )
    else:
        confirm_msg = "Your appointment is confirmed. A confirmation email was sent to your address."

    sms_note = ""
    if s.get("sms_opt_in") and p.get("phone"):
        digits = normalize_phone(p["phone"])
        if digits:
            sms_res = await send_sms_confirmation(
                to_phone_e164=to_e164_us(digits),
                message=build_booking_confirmation_sms_body(booking),
            )
            s["sms_sent"] = sms_res.ok
            s["sms_mock"] = sms_res.mock
            s["sms_last_error"] = sms_res.error if not sms_res.ok else None
            s["sms_message_sid"] = sms_delivery_ref(sms_res) if sms_res.ok and not sms_res.mock else None
            if sms_res.ok:
                sms_note = (
                    " (SMS simulated — set TEXTBELT_API_KEY or Twilio in backend/.env to send real texts.)"
                    if sms_res.mock
                    else " (SMS sent — check your phone; use Textbelt or Twilio logs if needed.)"
                )
            else:
                hint = f" {sms_res.error}" if sms_res.error else ""
                sms_note = f" (SMS failed.{hint})"
            replace_session(body.session_id, s)

    final = get_session(body.session_id)
    return BookingResponse(
        success=True,
        message=confirm_msg + sms_note,
        booking=booking,
        session=final or s,
        email_mock=email_mock,
        sms_mock=bool((final or s).get("sms_mock")),
    )
