"""Merge orchestrator output into session and refresh derived fields."""
from __future__ import annotations


from typing import Any

from app.services.provider_matcher import get_provider_by_id, match_provider_from_reason
from app.services.slot_service import filter_slots, slots_for_provider
from app.utils.validation import is_valid_email, normalize_phone, parse_dob


def merge_patient(session: dict[str, Any], patient_updates: dict[str, Any]) -> None:
    p = session["patient"]
    for key in ("first_name", "last_name", "phone", "email"):
        if key in patient_updates and patient_updates[key] is not None:
            val = str(patient_updates[key]).strip()
            if val:
                p[key] = val
    if "dob" in patient_updates and patient_updates["dob"] is not None:
        dob = patient_updates["dob"]
        if isinstance(dob, str):
            parsed = parse_dob(dob)
            if parsed:
                p["dob"] = parsed


def intake_is_complete(session: dict[str, Any]) -> bool:
    p = session["patient"]
    return bool(
        p.get("first_name")
        and p.get("last_name")
        and p.get("dob")
        and p.get("phone")
        and p.get("email")
        and is_valid_email(p["email"])
        and normalize_phone(p["phone"])
    )


def refresh_after_reason(session: dict[str, Any]) -> None:
    reason = session.get("reason_for_visit")
    if not reason:
        session["matched_provider_id"] = None
        session["matched_provider"] = None
        return
    prov, err = match_provider_from_reason(reason)
    if prov:
        session["matched_provider_id"] = prov["id"]
        session["matched_provider"] = prov
        session["match_error"] = None
    else:
        session["matched_provider_id"] = None
        session["matched_provider"] = None
        session["match_error"] = err


def refresh_slots(session: dict[str, Any]) -> None:
    pid = session.get("matched_provider_id")
    if not pid:
        session["shown_slots"] = []
        return
    raw = slots_for_provider(pid)
    q = session.get("slot_query") or ""
    session["shown_slots"] = filter_slots(raw, q if q else None, max_results=12)


def apply_session_updates(session: dict[str, Any], updates: dict[str, Any]) -> None:
    """Mutates session in place."""
    if not updates:
        return
    if "workflow" in updates and updates["workflow"] is not None:
        session["workflow"] = updates["workflow"]
    if "patient" in updates and isinstance(updates["patient"], dict):
        merge_patient(session, updates["patient"])
    if "reason_for_visit" in updates and updates["reason_for_visit"] is not None:
        session["reason_for_visit"] = str(updates["reason_for_visit"]).strip()
    if "slot_query" in updates:
        session["slot_query"] = updates["slot_query"]
    if "selected_slot_id" in updates:
        session["selected_slot_id"] = updates["selected_slot_id"]
    if "intake_complete" in updates:
        session["intake_complete"] = bool(updates["intake_complete"])
    if "refill" in updates and isinstance(updates["refill"], dict):
        session["refill"] = {**session["refill"], **updates["refill"]}
    if "sms_opt_in" in updates and updates["sms_opt_in"] is not None:
        session["sms_opt_in"] = bool(updates["sms_opt_in"])
    if "refill_complete" in updates:
        session["refill_complete"] = bool(updates["refill_complete"])

    if session.get("reason_for_visit"):
        refresh_after_reason(session)
    if session.get("workflow") == "scheduling":
        refresh_slots(session)

    if "intake_complete" not in updates:
        session["intake_complete"] = intake_is_complete(session)


def recompute_derived(session: dict[str, Any]) -> None:
    if session.get("matched_provider_id"):
        session["matched_provider"] = get_provider_by_id(session["matched_provider_id"])
    refresh_slots(session)
