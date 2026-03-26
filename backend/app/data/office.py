"""Hard-coded practice office details."""
from __future__ import annotations

from typing import Any, Dict, Optional


OFFICE = {
    "name": "Kyron Medical — Main Campus",
    "address_line1": "1200 Kyron Medical Plaza",
    "address_line2": "Suite 400",
    "city": "Austin",
    "state": "TX",
    "zip": "78701",
    "phone": "(512) 555-0142",
    "hours": {
        "monday": "8:00 AM – 5:30 PM",
        "tuesday": "8:00 AM – 5:30 PM",
        "wednesday": "8:00 AM – 5:30 PM",
        "thursday": "8:00 AM – 5:30 PM",
        "friday": "8:00 AM – 4:00 PM",
        "saturday": "Closed",
        "sunday": "Closed",
    },
    "parking": "Complimentary patient parking in the garage on Level P2.",
    "notes": "Please arrive 15 minutes early for check-in and bring a photo ID and insurance card.",
}


def office_voice_facts_paragraph(office: Optional[Dict[str, Any]] = None) -> str:
    """Single block for voice prompts / Vapi variables — Kyron-only canonical office facts."""
    o = office if office else OFFICE
    name = str(o.get("name") or "Kyron Medical")
    a1 = str(o.get("address_line1") or "")
    a2 = (o.get("address_line2") or "").strip()
    city = str(o.get("city") or "")
    state = str(o.get("state") or "")
    z = str(o.get("zip") or "")
    phone = str(o.get("phone") or "")
    line2 = f", {a2}" if a2 else ""
    addr = f"{a1}{line2}, {city}, {state} {z}".strip()
    hours = o.get("hours") or {}
    hour_lines = [f"{day.capitalize()}: {span}" for day, span in hours.items()]
    parking = (o.get("parking") or "").strip()
    notes = (o.get("notes") or "").strip()
    parts = [
        f"Practice: {name}.",
        f"Address: {addr}.",
        f"Main phone: {phone}.",
        "Hours:",
        *hour_lines,
    ]
    if parking:
        parts.append(f"Parking: {parking}")
    if notes:
        parts.append(f"Check-in: {notes}")
    return "\n".join(parts)
