"""Create booking record from selected slot."""
from __future__ import annotations


from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.data.office import OFFICE
from app.data.slot_generator import ALL_MOCK_SLOTS
from app.services.provider_matcher import get_provider_by_id


def find_slot(slot_id: str) -> Optional[Dict[str, Any]]:
    for s in ALL_MOCK_SLOTS:
        if s["id"] == slot_id:
            return s
    return None


def create_booking(session: Dict[str, Any], slot_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    slot = find_slot(slot_id)
    if not slot:
        return False, "That time slot is not available.", None

    # For direct/voice calls (PhoneCallCard) matched_provider_id may not be set yet —
    # accept the slot from any provider and record it onto the session in that case.
    if session.get("matched_provider_id"):
        if slot["provider_id"] != session["matched_provider_id"]:
            return False, "That time slot is not available for the selected provider.", None
    else:
        # Bind session to the provider that owns the chosen slot.
        session["matched_provider_id"] = slot["provider_id"]

    prov = get_provider_by_id(slot["provider_id"])
    if not prov:
        return False, "Provider not found.", None

    start = datetime.fromisoformat(slot["start_iso"])
    booking = {
        "slot_id": slot_id,
        "provider_id": prov["id"],
        "provider_name": prov["full_name"],
        "specialty": prov["specialty"],
        "start_iso": slot["start_iso"],
        "end_iso": slot["end_iso"],
        "office_name": OFFICE["name"],
        "office_address": f"{OFFICE['address_line1']}, {OFFICE['city']}, {OFFICE['state']} {OFFICE['zip']}",
        "office_phone": OFFICE["phone"],
        "confirmed_at": datetime.utcnow().isoformat() + "Z",
    }
    return True, "Booked.", booking
