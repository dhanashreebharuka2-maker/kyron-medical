"""Voice handoff: structured context for outbound voice (e.g. Vapi)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.data.office import OFFICE, office_voice_facts_paragraph
from app.services.booking_service import find_slot
from app.services.slot_service import slots_for_provider
from app.services.voice_providers.alex_prompts import ALEX_SYSTEM_PROMPT


def _workflow_stage(session: dict[str, Any]) -> str:
    if session.get("booking_confirmed") and session.get("booking"):
        return "booking_complete"
    if session.get("selected_slot_id"):
        return "slot_selected"
    if session.get("workflow") == "scheduling" and session.get("intake_complete"):
        return "scheduling_choosing_slot"
    if session.get("workflow") == "scheduling":
        return "scheduling_intake"
    if session.get("refill_complete"):
        return "refill_submitted"
    if session.get("workflow") == "refill":
        return "refill_in_progress"
    if session.get("workflow") == "office":
        return "office_info"
    return "general"


def _truncate(s: str, max_len: int = 280) -> str:
    t = (s or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _conversation_turns(messages: List[dict[str, Any]], max_turns: int = 8) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for m in messages[-max_turns:]:
        role = m.get("role")
        content = m.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        out.append({"role": role, "content": _truncate(content, 400)})
    return out


def _voice_intake_blocking_block(structured: Dict[str, Any]) -> str:
    """
    Explicit instructions so the model does not read slots first (common failure when web intake exists).
    """
    p = structured.get("patient") or {}
    fn = (p.get("first_name") or "").strip()
    ln = (p.get("last_name") or "").strip()
    dob = (p.get("dob") or "").strip()
    reason = (structured.get("reason_for_visit") or "").strip()
    lines = [
        "## Voice intake — BLOCKING (complete this before any appointment times)",
        "Do not say Option 1, Option 2, any numbered option, any weekday, or any clock time for an appointment until this step is finished on the call.",
        "On the call, collect or confirm one-by-one: first name, last name, date of birth, reason for visit.",
    ]
    if fn and ln and dob and reason:
        lines.append(
            f"The web session may already list: {fn} {ln}, DOB {dob}, reason: {_truncate(str(reason), 160)}. "
            "Do NOT read slots next. Tell the caller you have details from their online visit and ask them to confirm or correct "
            "each item, one question at a time. Only after all four are confirmed may you introduce the provider and read the slot list."
        )
    else:
        missing: List[str] = []
        if not fn:
            missing.append("first name")
        if not ln:
            missing.append("last name")
        if not dob:
            missing.append("date of birth")
        if not reason:
            missing.append("reason for visit")
        lines.append(
            f"These are still missing or incomplete — ask for them on the call: {', '.join(missing)}. "
            "Do not read the numbered appointment list until all four are collected."
        )
    return "\n".join(lines)


def _voice_sms_blocking_block(structured: Dict[str, Any]) -> str:
    """Keep SMS consent in-model even when the call runs long — must happen before goodbye."""
    p = structured.get("patient") or {}
    last4 = (p.get("phone_last4") or "").strip() or "the number on this session"
    return "\n".join(
        [
            "## SMS text confirmation — BLOCKING (after verbal booking, before anything else)",
            "After you confirm the appointment time by voice and give the 15-minute early arrival + photo ID reminders, you **must** ask whether they want a **text message confirmation** "
            f"sent to their mobile on file (last four digits: **{last4}**). Wait for yes or no.",
            "Do **not** ask “anything else,” do **not** say thank-you/goodbye, and do **not** end the call until this SMS question is asked and answered.",
            "If your assistant has the **kyron_sms_opt_in** tool, call it once with **session_id** = the `kyron_session_id` variable and **opt_in** true or false matching their answer.",
        ]
    )


def _conversation_summary(messages: List[dict[str, Any]], max_bullets: int = 5) -> str:
    turns = _conversation_turns(messages, max_turns=12)
    if not turns:
        return "No prior chat messages in this session."
    lines: List[str] = []
    for t in turns[-max_bullets:]:
        prefix = "Patient said" if t["role"] == "user" else "Assistant replied"
        lines.append(f"- {prefix}: {_truncate(t['content'], 120)}")
    return "Recent web chat (most recent last):\n" + "\n".join(lines)


def _selected_slot_detail(session: dict[str, Any]) -> Optional[Dict[str, Any]]:
    sid = session.get("selected_slot_id")
    if not sid:
        return None
    slot = find_slot(str(sid))
    if not slot:
        return {"id": str(sid), "start_iso": None, "note": "Slot id present but details unavailable."}
    return {
        "id": slot["id"],
        "start_iso": slot["start_iso"],
        "end_iso": slot.get("end_iso"),
        "duration_minutes": slot.get("duration_minutes"),
        "provider_id": slot.get("provider_id"),
    }


def _slot_start_dt(slot: Dict[str, Any]) -> datetime:
    return datetime.fromisoformat(slot["start_iso"])


def _slot_voice_label(start_iso: str) -> str:
    dt = datetime.fromisoformat(start_iso)
    h = dt.strftime("%I").lstrip("0") or "12"
    mm = dt.strftime("%M")
    ampm = dt.strftime("%p")
    return f"{dt.strftime('%A')}, {dt.strftime('%B')} {dt.day} at {h}:{mm} {ampm}"


def _build_offered_slots(session: dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
    """
    Real upcoming mock slots for the matched provider (or the web chat's shown_slots list)
    so the voice model can read concrete times — not improvise.
    """
    now = datetime.now()
    candidates: List[Dict[str, Any]] = []

    pid = session.get("matched_provider_id")
    shown = session.get("shown_slots") or []

    if pid:
        raw = slots_for_provider(str(pid))
        candidates = [s for s in raw if _slot_start_dt(s) >= now]
        candidates.sort(key=lambda s: s["start_iso"])
    elif isinstance(shown, list) and shown:
        candidates = [
            s
            for s in shown
            if isinstance(s, dict) and s.get("start_iso") and s.get("id") and _slot_start_dt(s) >= now
        ]
        candidates.sort(key=lambda s: s["start_iso"])

    out: List[Dict[str, Any]] = []
    for i, s in enumerate(candidates[:limit], start=1):
        start_iso = str(s["start_iso"])
        out.append(
            {
                "ordinal": i,
                "id": str(s["id"]),
                "start_iso": start_iso,
                "label_voice": _slot_voice_label(start_iso),
                "provider_id": str(s.get("provider_id") or ""),
            }
        )
    return out


def _offered_slots_paragraph(offered: List[Dict[str, Any]]) -> str:
    if not offered:
        return (
            "No specific appointment openings are listed for this call (there is no matched Kyron provider "
            "and no slot list from the website session). Offer Kyron's main phone and office hours from the "
            "canonical office section, or suggest continuing scheduling in the same web chat session."
        )
    lines = [
        "WAIT — do NOT read these times until intake is fully complete on this call (first name, last name, DOB, reason for visit all confirmed).",
        "Once intake is done, immediately say: 'We have the following openings available' and read the list below — do NOT mention the provider name, specialty, or department.",
        "Do not invent or modify any times. Read exactly as listed:",
    ]
    for o in offered:
        lines.append(f"Option {o['ordinal']}: {o['label_voice']}.")
    lines.append(
        "After reading all options ask: 'Which option works best for you?' "
        "When they pick one, repeat the day and time back once to confirm."
    )
    return "\n".join(lines)


def build_structured_voice_context(session: dict[str, Any], phone_digits: str) -> Dict[str, Any]:
    """Structured payload for voice (Vapi metadata + webhook completion, etc.)."""
    p = session.get("patient") or {}
    prov = session.get("matched_provider") or {}
    booking = session.get("booking")
    refill = session.get("refill") or {}
    messages = session.get("messages") or []

    phone_e164 = f"+1{phone_digits}"
    phone_last4 = phone_digits[-4:] if len(phone_digits) >= 4 else phone_digits

    matched_out: Optional[Dict[str, Any]] = None
    if prov or session.get("matched_provider_id"):
        matched_out = {
            "id": prov.get("id") or session.get("matched_provider_id"),
            "full_name": prov.get("full_name"),
            "specialty": prov.get("specialty"),
        }

    offered_slots = _build_offered_slots(session, limit=8)

    return {
        "schema_version": 2,
        "session_id": session.get("session_id"),
        "workflow_stage": _workflow_stage(session),
        "patient": {
            "first_name": p.get("first_name"),
            "last_name": p.get("last_name"),
            "dob": p.get("dob"),
            "phone_e164": phone_e164,
            "phone_last4": phone_last4,
            "email": p.get("email"),
        },
        "reason_for_visit": session.get("reason_for_visit"),
        "matched_provider": matched_out,
        "match_error": session.get("match_error"),
        "selected_slot": _selected_slot_detail(session),
        "booking": (
            {
                "confirmed": True,
                "provider_name": booking.get("provider_name"),
                "start_iso": booking.get("start_iso"),
                "office_name": booking.get("office_name"),
                "office_phone": booking.get("office_phone"),
            }
            if booking
            else None
        ),
        "refill": (
            {
                "medication": refill.get("medication"),
                "notes": refill.get("notes"),
                "pharmacy": refill.get("pharmacy"),
                "urgency": refill.get("urgency"),
                "submitted": bool(session.get("refill_complete")),
            }
            if session.get("workflow") == "refill" or session.get("refill_complete")
            else None
        ),
        "recent_conversation": _conversation_turns(messages),
        "conversation_summary": _conversation_summary(messages),
        "kyron_office": session.get("office") or OFFICE,
        "offered_slots": offered_slots,
        "offered_slots_paragraph": _offered_slots_paragraph(offered_slots),
    }


def build_continuation_prompt(structured: Dict[str, Any]) -> str:
    """Full Alex instructions plus live web-session facts for the voice task prompt."""
    stage = structured.get("workflow_stage") or "general"
    p = structured.get("patient") or {}
    name = f"{p.get('first_name') or ''} {p.get('last_name') or ''}".strip() or "the patient"
    prov = structured.get("matched_provider") or {}
    prov_line = ""
    if prov and prov.get("id"):
        # Internal routing context only — do NOT say the provider name, specialty, or department out loud.
        prov_line = "[INTERNAL: provider matched for this session — do not speak provider name or specialty aloud] "
    reason = structured.get("reason_for_visit")
    reason_line = f"Reason for visit: {_truncate(str(reason), 200)}. " if reason else ""

    booking = structured.get("booking")
    book_line = ""
    if booking:
        book_line = (
            f"Booking confirmed for {booking.get('start_iso')} with {booking.get('provider_name')}. "
        )
    elif structured.get("selected_slot"):
        ss = structured["selected_slot"]
        book_line = f"Selected slot (not yet confirmed in this session): {ss.get('start_iso')}. "

    refill = structured.get("refill")
    refill_line = ""
    if refill and refill.get("submitted"):
        refill_line = f"Refill submitted for {refill.get('medication')}. "
    elif refill:
        refill_line = "Refill workflow in progress on web. "

    office = structured.get("kyron_office") or OFFICE
    office_block = office_voice_facts_paragraph(office if isinstance(office, dict) else None)
    slots_block = str(structured.get("offered_slots_paragraph") or "")
    offered_raw = structured.get("offered_slots")
    offered_count = len(offered_raw) if isinstance(offered_raw, list) else 0

    booking_callout = ""
    if offered_count > 0:
        booking_callout = (
            "## Booking flow reminder (this call)\n"
            "Intake on the phone comes first — see BLOCKING section above. "
            "Only after intake is complete, **immediately** say 'We have the following openings available' and read the numbered slots from the last section. "
            "Do NOT say the provider name, specialty, or department — just read the numbered time options. "
            "Do not say wait/hold or pretend to look up times; they are already listed below. "
            "Then confirm choice, arrival 15 minutes early, and photo ID.\n\n"
        )

    intake_block = _voice_intake_blocking_block(structured)
    sms_blocking = _voice_sms_blocking_block(structured)

    kyron_sid = structured.get("session_id")
    sms_tool_block = ""
    if kyron_sid:
        sms_tool_block = (
            "## SMS text confirmation (session id for Vapi tools)\n"
            f"Use this exact **session_id** when calling **kyron_sms_opt_in** (same value as variable **kyron_session_id**): `{kyron_sid}`\n\n"
        )

    facts = (
        f"{intake_block}\n\n"
        f"{sms_blocking}\n\n"
        f"{sms_tool_block}"
        "## Canonical Kyron Medical office (only source for address / phone / hours on this call)\n"
        f"{office_block}\n\n"
        f"{booking_callout}"
        "## Live web session (reference — still require phone intake before slots)\n"
        f"Workflow stage: {stage}. Patient: {name}. "
        f"Email: {p.get('email') or 'unknown'}. DOB: {p.get('dob') or 'unknown'}. "
        f"{reason_line}{prov_line}{book_line}{refill_line}\n"
        f"{structured.get('conversation_summary') or ''}\n\n"
        "## Upcoming appointment openings for this call (read last — only after intake is complete)\n"
        f"{slots_block}"
    )
    return f"{ALEX_SYSTEM_PROMPT}\n\n{facts}"


def build_voice_handoff_bundle(
    session: dict[str, Any],
    phone_digits: str,
) -> Tuple[Dict[str, Any], str, Dict[str, Any], str]:
    """
    Returns (handoff_metadata, voice_context_summary, structured_context, continuation_prompt).
    """
    structured = build_structured_voice_context(session, phone_digits)
    continuation = build_continuation_prompt(structured)

    p = structured.get("patient") or {}
    summary_lines = [
        "Kyron Medical — Alex voice handoff (Vapi + session context).",
        f"Stage: {structured['workflow_stage']}",
        f"Patient: {p.get('first_name') or ''} {p.get('last_name') or ''}".strip(),
        f"Phone: {p.get('phone_e164')}",
        f"Email: {p.get('email') or 'n/a'}",
        f"DOB: {p.get('dob') or 'n/a'}",
        f"Reason for visit: {structured.get('reason_for_visit') or 'n/a'}",
    ]
    mp = structured.get("matched_provider")
    if mp and mp.get("full_name"):
        summary_lines.append(f"Provider: {mp.get('full_name')} ({mp.get('specialty')})")
    if structured.get("selected_slot"):
        summary_lines.append(f"Selected slot: {structured['selected_slot'].get('start_iso')}")
    if structured.get("offered_slots"):
        summary_lines.append(f"Voice offered slots: {len(structured['offered_slots'])} openings packaged for readout")
    if structured.get("booking"):
        summary_lines.append(f"Booking: confirmed {structured['booking'].get('start_iso')}")
    if structured.get("refill"):
        summary_lines.append(f"Refill: {structured['refill']}")

    summary_lines.append("Safety: no medical advice; admin scheduling/refill routing only.")
    voice_summary = "\n".join(line for line in summary_lines if line)

    handoff_metadata = {
        "voice_provider": "vapi",
        "destination_e164": structured["patient"]["phone_e164"],
        "session_id": session.get("session_id"),
        "continuation_prompt": continuation,
        "raw_session_snapshot": {
            "workflow": session.get("workflow"),
            "matched_provider_id": session.get("matched_provider_id"),
            "selected_slot_id": session.get("selected_slot_id"),
            "booking_confirmed": session.get("booking_confirmed"),
            "intake_complete": session.get("intake_complete"),
        },
    }

    return handoff_metadata, voice_summary, structured, continuation
