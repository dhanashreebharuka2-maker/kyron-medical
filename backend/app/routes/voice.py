from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException

from app.schemas.notifications import SmsOptInRequest, SmsSendResponse
from app.schemas.voice import (
    VoiceChooseSlotRequest,
    VoiceHandoffRequest,
    VoiceHandoffResponse,
)
from app.routes.notifications import apply_sms_opt_in
from app.services.booking_service import create_booking, find_slot
from app.services.email_service import send_booking_confirmation_email
from app.data.providers import PROVIDERS
from app.services.session_logic import recompute_derived, refresh_after_reason, refresh_slots
from app.services.slot_service import slots_for_provider
from app.services.session_service import get_session, replace_session
from app.services.sms_service import (
    build_booking_confirmation_sms_body,
    send_sms_confirmation,
    sms_delivery_ref,
    to_e164_us,
)
from app.services.voice_providers.vapi import initiate_vapi_handoff, vapi_fully_configured
from app.services.voice_service import build_voice_handoff_bundle
from app.services.voice_transcript_booking import infer_slot_ordinal_from_transcript, resolve_transcript_text
from app.utils.validation import normalize_phone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["voice"])


@router.post("/voice/sms-opt-in", response_model=SmsSendResponse)
async def voice_sms_opt_in(body: SmsOptInRequest):
    """
    Same behavior as POST /api/notify/sms-opt-in — intended for a Vapi **HTTP / server** tool
    (not Vapi's Twilio SMS widget). Textbelt/Twilio send from the backend after opt-in + booking.
    """
    return await apply_sms_opt_in(body)


def _nested_dict_blobs(payload: Any, max_nodes: int = 250) -> list[dict[str, Any]]:
    """Flatten nested dict/list webhook JSON for metadata / tool field discovery."""
    out: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return out
    queue: list[tuple[dict[str, Any], int]] = [(payload, 0)]
    seen: set[int] = set()
    while queue and len(out) < max_nodes:
        obj, depth = queue.pop(0)
        oid = id(obj)
        if oid in seen or depth > 10:
            continue
        seen.add(oid)
        out.append(obj)
        if depth >= 10:
            continue
        for v in obj.values():
            if isinstance(v, dict):
                queue.append((v, depth + 1))
            elif isinstance(v, list):
                for item in v[:50]:
                    if isinstance(item, dict):
                        queue.append((item, depth + 1))
    return out


def _metadata_from_voice_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Merge all `metadata` dicts found in the webhook tree."""
    merged: dict[str, Any] = {}
    for blob in _nested_dict_blobs(payload):
        m = blob.get("metadata")
        if isinstance(m, dict) and m:
            merged.update(m)
    return merged


def _session_id_from_voice_payload(payload: dict[str, Any]) -> Optional[str]:
    # 1. Check all merged metadata dicts (covers call.metadata, message.metadata, etc.)
    meta = _metadata_from_voice_payload(payload)
    for key in ("kyron_session_id", "session_id", "sessionId"):
        v = meta.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()

    # 2. Deep search across entire payload tree for kyron_session_id / session_id
    found = _deep_find_first(payload, {"kyron_session_id", "session_id", "sessionId"})
    if found is not None and str(found).strip():
        return str(found).strip()

    # 3. Check variableValues (Vapi may echo assistantOverrides.variableValues in the report)
    for blob in _nested_dict_blobs(payload):
        vv = blob.get("variableValues") or blob.get("variable_values")
        if isinstance(vv, dict):
            for key in ("kyron_session_id", "session_id"):
                v = vv.get(key)
                if v is not None and str(v).strip():
                    return str(v).strip()

    return None


def _as_positive_int(val: Any) -> Optional[int]:
    if isinstance(val, bool):
        return None
    if isinstance(val, int) and val > 0:
        return val
    if isinstance(val, str):
        s = val.strip().lower()
        if s.isdigit():
            n = int(s)
            return n if n > 0 else None
        m = re.search(r"\b(\d+)\b", s)
        if m:
            n = int(m.group(1))
            return n if n > 0 else None
    return None


def _deep_find_first(payload: Any, keys: set[str]) -> Optional[Any]:
    """Depth-first search for the first key match in nested dict/list payloads."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            if k in keys and v is not None:
                return v
        for v in payload.values():
            found = _deep_find_first(v, keys)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _deep_find_first(item, keys)
            if found is not None:
                return found
    return None


def _as_bool(val: Any) -> Optional[bool]:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("true", "1", "yes", "y"):
            return True
        if s in ("false", "0", "no", "n"):
            return False
    return None


async def _finalize_booking_and_notifications(session_id: str, slot_id: str) -> dict[str, Any]:
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "session not found")

    existing = s.get("booking") if s.get("booking_confirmed") else None
    if existing and existing.get("slot_id") != slot_id:
        raise HTTPException(
            400,
            "Session already has a confirmed booking for a different time; clear it in-session before rebooking.",
        )

    if existing and existing.get("slot_id") == slot_id:
        booking = existing
    else:
        ok, err, booking = create_booking(s, slot_id)
        if not ok or not booking:
            raise HTTPException(400, err or "booking failed")
        s["booking"] = booking
        s["booking_confirmed"] = True
        s["selected_slot_id"] = slot_id
        recompute_derived(s)
        replace_session(session_id, s)

    p = s["patient"]
    name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or "Patient"

    if not s.get("email_sent"):
        email_ok, email_mock = await send_booking_confirmation_email(
            p.get("email") or "",
            name,
            booking["provider_name"],
            booking["specialty"],
            booking["start_iso"],
        )
        s["email_sent"] = email_ok
        s["email_mock"] = email_mock
        replace_session(session_id, s)

    sms_sent = bool(s.get("sms_sent"))
    sms_mock = bool(s.get("sms_mock"))
    sms_error: Optional[str] = s.get("sms_last_error")

    logger.info(
        "SMS gate check — session=%s sms_opt_in=%s phone=%s sms_sent=%s",
        session_id,
        s.get("sms_opt_in"),
        bool(p.get("phone")),
        s.get("sms_sent"),
    )
    if s.get("sms_opt_in") and p.get("phone") and not s.get("sms_sent"):
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
            replace_session(session_id, s)
            sms_sent = sms_res.ok
            sms_mock = sms_res.mock
            sms_error = sms_res.error

    latest = get_session(session_id) or s
    return {
        "success": True,
        "message": "Voice booking confirmed; backend confirmation notifications processed.",
        "booking": booking,
        "session_id": session_id,
        "email_sent": bool((latest or {}).get("email_sent")),
        "email_mock": bool((latest or {}).get("email_mock")),
        "sms_sent": sms_sent,
        "sms_mock": sms_mock,
        "sms_error": sms_error,
        "session": latest,
    }


@router.post("/voice/handoff", response_model=VoiceHandoffResponse)
async def voice_handoff(body: VoiceHandoffRequest):
    s = get_session(body.session_id)
    if not s:
        raise HTTPException(404, "session not found")

    phone = body.patient_phone_override or (s.get("patient") or {}).get("phone")
    digits = normalize_phone(phone or "")
    if not digits:
        raise HTTPException(400, "A valid US phone number is required for voice handoff.")

    # Normalize into session so post-call SMS and webhook finalization always see the same 10-digit US number.
    patient = {**(s.get("patient") or {}), "phone": digits}
    s["patient"] = patient
    replace_session(body.session_id, s)
    s = get_session(body.session_id) or s

    refresh_after_reason(s)
    refresh_slots(s)

    # For direct calls (PhoneCallCard — no chat context), pre-load upcoming slots for ALL providers
    # so Alex can offer real times after collecting intake on the call.
    if not s.get("matched_provider_id") and not s.get("shown_slots"):
        from datetime import datetime as _dt
        now = _dt.now()
        all_slots = []
        for prov in PROVIDERS:
            raw = slots_for_provider(prov["id"])
            future = [sl for sl in raw if _dt.fromisoformat(sl["start_iso"]) >= now]
            future.sort(key=lambda sl: sl["start_iso"])
            all_slots.extend(future[:3])
        s["shown_slots"] = all_slots
        logger.info("Direct call: pre-loaded %d slots across all providers for session %s", len(all_slots), body.session_id)

    replace_session(body.session_id, s)
    s = get_session(body.session_id) or s

    handoff_metadata, summary, structured, continuation = build_voice_handoff_bundle(s, digits)
    s["voice_offered_slots"] = structured.get("offered_slots") or []

    demo_mode = not vapi_fully_configured()
    voice_call_placed = False
    voice_call_id: str | None = None
    voice_error: str | None = None

    if demo_mode:
        msg = (
            "Your chat context is ready for a voice continuation. "
            "Demo mode: no outbound call was placed. Add VAPI_API_KEY, VAPI_ASSISTANT_ID, VAPI_PHONE_NUMBER_ID, and VAPI_WEBHOOK_URL to the backend."
        )
    else:
        result = await initiate_vapi_handoff(f"+1{digits}", structured, continuation)
        demo_mode = result.demo_mode
        if not result.ok:
            voice_error = result.error or "Vapi request failed"
            s["voice_handoff"] = {
                **handoff_metadata,
                "structured_context": structured,
                "voice_call_id": None,
                "voice_error": voice_error,
            }
            s["voice_handoff_ready"] = True
            s["voice_handoff_at"] = datetime.now(timezone.utc).isoformat()
            replace_session(body.session_id, s)
            raise HTTPException(502, voice_error)
        voice_call_placed = True
        voice_call_id = result.call_id
        s["voice_last_call_id"] = voice_call_id
        msg = (
            "Calling you now — the voice assistant has your chat context and will continue where you left off."
        )

    s["voice_handoff"] = {
        **handoff_metadata,
        "structured_context": structured,
        "voice_call_id": voice_call_id,
        "voice_error": voice_error,
    }
    s["voice_handoff_ready"] = True
    s["voice_handoff_at"] = datetime.now(timezone.utc).isoformat()
    replace_session(body.session_id, s)

    updated = get_session(body.session_id) or s
    handoff_payload = updated.get("voice_handoff") or {}

    return VoiceHandoffResponse(
        success=True,
        message=msg,
        handoff_payload=handoff_payload if isinstance(handoff_payload, dict) else {},
        voice_context_summary=summary,
        structured_context=structured,
        continuation_prompt=continuation,
        demo_mode=demo_mode,
        voice_call_placed=voice_call_placed,
        voice_call_id=voice_call_id,
        voice_error=voice_error,
        session=updated,
    )


def apply_voice_slot_choice(session_id: str, slot_ordinal: int) -> dict[str, Any]:
    """
    Map a 1-based option index from the voice-offered list to selected_slot_id on the session.
    """
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "session not found")
    if not s.get("matched_provider_id"):
        raise HTTPException(400, "No matched provider for this session; choose-slot requires scheduling context.")

    offers = s.get("voice_offered_slots") or []
    match = next((x for x in offers if isinstance(x, dict) and x.get("ordinal") == slot_ordinal), None)
    if not match:
        raise HTTPException(400, "Unknown slot option for this session.")
    slot_id = str(match["id"])
    slot = find_slot(slot_id)
    if not slot or slot["provider_id"] != s.get("matched_provider_id"):
        raise HTTPException(400, "That time is not valid for the matched provider.")

    s["selected_slot_id"] = slot_id
    replace_session(session_id, s)
    return {"success": True, "selected_slot_id": slot_id, "message": "Slot choice recorded."}


@router.post("/voice/choose-slot")
async def voice_choose_slot(body: VoiceChooseSlotRequest):
    """Record the caller's choice from the numbered voice slot list (manual integration)."""
    return apply_voice_slot_choice(body.session_id, body.slot_ordinal)


async def _process_voice_completion(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Shared post-call path: webhook body or GET /v1/calls/{id} JSON.

    Resolution order: explicit slot_id in payload/metadata → slot_ordinal in payload →
    session.selected_slot_id → call transcript + infer_slot_ordinal_from_transcript.
    """
    confirmed_raw = _deep_find_first(
        payload,
        {
            "appointment_confirmed",
            "appointmentConfirmed",
            "booking_confirmed",
            "bookingConfirmed",
            "confirmed",
        },
    )
    confirmed = _as_bool(confirmed_raw)
    if confirmed is False:
        return {"success": True, "message": "Explicit not-confirmed; no booking action taken."}

    s = get_session(session_id) or {}
    meta = _metadata_from_voice_payload(payload)

    slot_id = _deep_find_first(payload, {"slot_id", "slotId", "selected_slot_id", "selectedSlotId"})
    if not slot_id and meta:
        sid = meta.get("selected_slot_id") or meta.get("slot_id")
        if sid is not None and str(sid).strip():
            slot_id = str(sid).strip()

    ordinal: Optional[int] = None
    if not slot_id or not isinstance(slot_id, str):
        ord_raw = _deep_find_first(
            payload,
            {
                "slot_ordinal",
                "slotOrdinal",
                "chosen_option",
                "chosenOption",
                "appointment_option",
                "appointmentOption",
            },
        )
        ordinal = _as_positive_int(ord_raw)
        if ordinal is None:
            for blob in _nested_dict_blobs(payload):
                for key in ("slot_ordinal", "slotOrdinal", "chosenOption", "chosen_option"):
                    if key in blob:
                        ordinal = _as_positive_int(blob[key])
                        break
                if ordinal is not None:
                    break
        if ordinal is not None:
            for item in s.get("voice_offered_slots") or []:
                if isinstance(item, dict) and item.get("ordinal") == ordinal:
                    cand = item.get("id")
                    if cand:
                        slot_id = str(cand)
                    break

    if not slot_id or not isinstance(slot_id, str):
        slot_id = s.get("selected_slot_id")
    if not slot_id or not isinstance(slot_id, str):
        live = get_session(session_id) or s
        offers = live.get("voice_offered_slots") or []
        transcript = await resolve_transcript_text(payload)
        logger.info(
            "Voice completion transcript_len=%s offers_count=%s session_id=%s",
            len(transcript) if transcript else 0,
            len(offers),
            session_id,
        )
        if transcript and offers:
            ord_inf = infer_slot_ordinal_from_transcript(transcript, offers)
            if ord_inf is not None:
                for item in offers:
                    if isinstance(item, dict) and item.get("ordinal") == ord_inf:
                        cand = item.get("id")
                        if cand:
                            slot_id = str(cand)
                            logger.info(
                                "Voice completion: transcript inferred ordinal=%s slot_id=%s",
                                ord_inf,
                                slot_id,
                            )
                            break
        elif transcript and not offers:
            logger.info(
            "Voice completion: transcript len=%s but voice_offered_slots empty; cannot infer option",
                len(transcript),
            )

    if not slot_id or not isinstance(slot_id, str):
        live = get_session(session_id)
        logger.warning(
            "Voice completion: no slot to finalize — no email/SMS. session_id=%s session_in_memory=%s "
            "selected_slot_id_on_session=%s merged_metadata_keys=%s",
            session_id,
            bool(live),
            (live or {}).get("selected_slot_id"),
            list(meta.keys()) if meta else [],
        )
        return {
            "success": True,
            "message": "No slot_id available; no booking action taken.",
            "kyron_hint": (
                "Pass kyron_session_id in the voice provider metadata; use Call me so voice_offered_slots is set; "
                "set OPENAI_API_KEY for transcript inference."
            ),
        }

    # Default SMS opt-in for voice completions: if the patient never explicitly opted out (sms_opt_in is
    # None — i.e. neither web checkbox nor kyron_sms_opt_in tool was called), treat as opted-in so they
    # receive a booking confirmation text when a phone number is on file.
    live_s = get_session(session_id)
    if live_s and live_s.get("sms_opt_in") is None and (live_s.get("patient") or {}).get("phone"):
        live_s["sms_opt_in"] = True
        replace_session(session_id, live_s)
        logger.info("Voice completion: sms_opt_in defaulted to True for session %s", session_id)

    return await _finalize_booking_and_notifications(session_id, str(slot_id).strip())


@router.post("/voice/vapi-webhook")
async def vapi_webhook(payload: dict[str, Any]):
    """
    Vapi post-call webhook: finalize booking and send the same confirmation email/SMS as web /book.

    Set VAPI_WEBHOOK_URL to this HTTPS route. We pass kyron_session_id in outbound call metadata.
    """
    # Vapi sends many event types during a call (transcript, status-update, function-call, etc.).
    # Only process the final end-of-call-report — ignore all mid-call events.
    event_type = (
        payload.get("type")
        or (payload.get("message") or {}).get("type")
        or ""
    )
    logger.info(
        "Vapi webhook event_type=%r top_keys=%s msg_keys=%s",
        event_type,
        list(payload.keys())[:8] if isinstance(payload, dict) else type(payload).__name__,
        list((payload.get("message") or {}).keys())[:8],
    )

    # Reject everything that is NOT the end-of-call summary.
    # If type is missing entirely, also skip — mid-call events never have booking data.
    if event_type != "end-of-call-report":
        return {"success": True, "message": f"Event '{event_type or 'unknown'}' acknowledged — no booking action."}

    # Dump the end-of-call payload so we can debug session_id extraction.
    import json as _json
    logger.warning("END-OF-CALL-REPORT payload (first 5000 chars): %s", _json.dumps(payload)[:5000])

    session_id = _session_id_from_voice_payload(payload)
    logger.warning("END-OF-CALL session_id extracted: %r", session_id)
    if not session_id:
        raise HTTPException(400, "Webhook payload missing session_id (metadata.kyron_session_id)")

    # Reuse the same transcript→slot inference and booking finalization path.
    return await _process_voice_completion(session_id, payload)
