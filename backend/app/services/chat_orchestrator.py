"""Chat turn: safety pre-check, OpenAI JSON orchestration, mock fallback."""
from __future__ import annotations


import re
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from app.data.office import OFFICE
from app.services.openai_client import run_json_orchestration
from app.services.session_logic import apply_session_updates, recompute_derived
from app.services.session_service import append_message, get_session, replace_session
from app.utils.validation import is_medical_advice_request


def _refill_intent_boilerplate(lower: str) -> bool:
    """True if the user is still asking for refill help, not naming a drug."""
    return bool(
        re.search(
            r"(need help|prescription refill|request a refill|need a refill|refill request|can i get a refill)",
            lower,
        )
    )


def _looks_like_medication_reply(session: dict[str, Any], text: str, lower: str) -> bool:
    """In refill flow, treat as medication name unless it's clearly another intent phrase."""
    if session.get("workflow") != "refill" or session.get("refill_complete"):
        return False
    t = text.strip()
    if len(t) < 2:
        return False
    if lower.strip() in ("no", "nope", "cancel", "stop", "help", "never mind"):
        return False
    # Strength / form on the label
    if re.search(r"\d", t) or re.search(r"\b(mg|ml|mcg|tablet|capsule|inhaler)\b", lower):
        return True
    # Only boilerplate intent — not a drug name yet
    if _refill_intent_boilerplate(lower) and len(t) < 80:
        return False
    # Likely drug name (word chars, not another workflow)
    if len(t) >= 4 and not re.search(
        r"\b(schedule|appointment|book|address|hours|location|office)\b", lower
    ):
        return True
    return False


def _emergency_reply(msg: str) -> Optional[str]:
    m = msg.lower()
    if any(
        x in m
        for x in (
            "chest pain",
            "can't breathe",
            "cannot breathe",
            "suicidal",
            "stroke",
            "unconscious",
            "severe bleeding",
        )
    ):
        return (
            "If you are having a medical emergency, call 911 or go to the nearest emergency room right away. "
            "I cannot schedule or assess emergencies here."
        )
    return None


def _mock_orchestrate(session: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Deterministic fallback when OpenAI is unavailable."""
    text = user_message.strip()
    lower = text.lower()
    updates: dict[str, Any] = {}

    # Refill before scheduling so phrases with both intents prefer refill routing.
    if any(k in lower for k in ("refill", "prescription", "medication", "pharmacy", "rx")):
        updates["workflow"] = "refill"

    if any(
        k in lower
        for k in ("schedule", "appointment", "book", "see a doctor", "visit", "availability")
    ):
        updates["workflow"] = "scheduling"

    if any(k in lower for k in ("address", "hours", "location", "phone", "where are you", "parking")):
        updates["workflow"] = "office"

    # Extract email
    em = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    if em:
        updates.setdefault("patient", {})["email"] = em.group(0)

    # Extract phone (simple)
    ph = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    if ph:
        digits = re.sub(r"\D", "", ph.group())
        if len(digits) >= 10:
            updates.setdefault("patient", {})["phone"] = ph.group()

    # Name patterns "I'm John Smith" / "name is Jane Doe"
    nm = re.search(
        r"(?:my name is|i am|i'm|name is)\s+([A-Za-z'-]+)\s+([A-Za-z'-]+)",
        text,
        re.I,
    )
    if nm:
        updates.setdefault("patient", {})["first_name"] = nm.group(1).title()
        updates.setdefault("patient", {})["last_name"] = nm.group(2).title()

    # Reason / symptoms
    if session.get("workflow") == "scheduling" or updates.get("workflow") == "scheduling":
        if len(text) > 15 and not em and not ph:
            # treat as reason if mentions body-ish words
            if any(
                w in lower
                for w in (
                    "pain",
                    "rash",
                    "hurt",
                    "knee",
                    "skin",
                    "chest",
                    "stomach",
                    "reflux",
                    "heart",
                    "bone",
                )
            ):
                updates["reason_for_visit"] = text

    slot_nl = (
        "morning",
        "afternoon",
        "evening",
        "tuesday",
        "monday",
        "wednesday",
        "thursday",
        "friday",
        "weekend",
        "weekday",
        "next week",
        "this week",
        "today",
        "tomorrow",
        "earliest",
        "soon",
        "asap",
        "before noon",
        "after 3",
        "next available",
    )
    if any(h in lower for h in slot_nl) or re.search(r"\b\d{1,2}\s*(am|pm)\b", lower):
        updates["slot_query"] = text

    # Refill: user named a medication — complete the request (avoid repeating "what medication?")
    if _looks_like_medication_reply(session, text, lower):
        updates["refill"] = {"medication": text.strip(), "notes": (session.get("refill") or {}).get("notes") or ""}
        updates["refill_complete"] = True

    reply_parts: List[str] = []

    if is_medical_advice_request(text):
        reply_parts.append(
            "I cannot provide medical advice or diagnoses. I can help with scheduling, routing a refill request to the "
            "practice, or sharing office information."
        )

    # Scheduling intent: distinct reply (mock was using the same default as "hi" before).
    if updates.get("workflow") == "scheduling":
        if session.get("workflow") != "scheduling":
            reply_parts.append(
                "I can help with that. I’ll walk you through a few quick questions in the chat to collect your name, "
                "date of birth, phone, email, and reason for your visit — then we can match a provider and show times."
            )
        else:
            reply_parts.append(
                "You’re set up for scheduling — continue the intake steps in the chat when you’re ready, and we’ll "
                "match a provider and show available times."
            )

    if updates.get("workflow") == "office" or session.get("workflow") == "office":
        reply_parts.append(
            f"Our office: {OFFICE['name']}, {OFFICE['address_line1']}, {OFFICE['city']}, {OFFICE['state']} "
            f"{OFFICE['zip']}. Phone: {OFFICE['phone']}. Hours: Mon–Fri 8–5:30 (Fri until 4)."
        )

    # Only when we just captured the medication this turn (not on every later message)
    if updates.get("refill_complete") and not session.get("refill_complete"):
        med = (updates.get("refill") or {}).get("medication") or "that medication"
        reply_parts.append(
            f"Thanks — I've recorded your refill request for {med}. Our team will review it. "
            "This assistant cannot approve refills; call the office if it's urgent."
        )
    elif updates.get("workflow") == "refill" or session.get("workflow") == "refill":
        updates.setdefault("refill", {})
        if "med" in lower or "pill" in lower or "drug" in lower:
            updates["refill"]["notes"] = text
        reply_parts.append(
            "I can record a refill request and route it to the practice. I cannot advise on medications or dosages. "
            "What medication are you asking about?"
        )

    # Short greetings when no workflow keyword matched (avoid duplicating the scheduling line above).
    if not reply_parts and len(text) <= 12 and lower.strip() in ("hi", "hello", "hey", "hi.", "hello.", "hey."):
        reply_parts.append(
            "Hi — I'm Alex, an AI assistant at Kyron Medical. I can help you schedule an appointment, route a refill "
            "request to the practice, or share our office address and hours. What would you like to do?"
        )

    if not reply_parts:
        reply_parts.append(
            "Hi — I'm Alex, an AI assistant at Kyron Medical. I can help you book an appointment, request a refill "
            "routing to the practice, or share our office address and hours. What would you like to do?"
        )

    return {
        "assistant_message": " ".join(reply_parts),
        "session_updates": updates,
    }


def process_chat(session_id: str, user_message: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    session = get_session(session_id)
    if not session:
        raise ValueError("invalid session")

    emerg = _emergency_reply(user_message)
    if emerg:
        append_message(session_id, "user", user_message)
        append_message(session_id, "assistant", emerg)
        s = get_session(session_id)
        assert s
        return emerg, s, {"emergency": True}

    append_message(session_id, "user", user_message)
    session_after_user = get_session(session_id)
    assert session_after_user
    recent = session_after_user.get("messages", [])

    raw = run_json_orchestration(session_after_user, user_message, recent)
    if not raw:
        raw = _mock_orchestrate(session_after_user, user_message)

    assistant_message = str(raw.get("assistant_message", "How can I help you today?"))
    updates = raw.get("session_updates") or {}

    base = get_session(session_id)
    assert base
    merged = deepcopy(base)
    apply_session_updates(merged, updates)
    recompute_derived(merged)

    replace_session(session_id, merged)
    append_message(session_id, "assistant", assistant_message)

    final = get_session(session_id)
    assert final

    ui_hints: Dict[str, Any] = {
        "show_intake": final.get("workflow") == "scheduling" and not final.get("intake_complete"),
        "show_refill": final.get("workflow") == "refill" and not final.get("refill_complete"),
        "show_provider": bool(final.get("matched_provider")),
        "show_slots": bool(
            final.get("workflow") == "scheduling"
            and final.get("intake_complete")
            and final.get("matched_provider_id")
        ),
        "match_error": final.get("match_error"),
    }

    return assistant_message, final, ui_hints
