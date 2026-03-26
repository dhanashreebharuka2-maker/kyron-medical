"""In-memory session store (swap for Redis/DB later)."""
from __future__ import annotations


import uuid
from copy import deepcopy
from typing import Any, Dict, Optional

from app.data.office import OFFICE

_sessions: Dict[str, Dict[str, Any]] = {}


def new_session() -> str:
    sid = str(uuid.uuid4())
    _sessions[sid] = {
        "session_id": sid,
        "workflow": None,  # scheduling | refill | office | general
        "patient": {
            "first_name": None,
            "last_name": None,
            "dob": None,
            "phone": None,
            "email": None,
        },
        "reason_for_visit": None,
        "matched_provider_id": None,
        "matched_provider": None,
        "intake_complete": False,
        "slot_query": None,
        "shown_slots": [],
        "selected_slot_id": None,
        "booking": None,
        "booking_confirmed": False,
        "email_sent": False,
        "sms_opt_in": None,
        "sms_sent": False,
        "sms_mock": False,
        "sms_last_error": None,
        "sms_message_sid": None,
        "refill": {"medication": None, "notes": None, "pharmacy": None, "urgency": None},
        "refill_complete": False,
        "voice_handoff": None,
        "voice_handoff_ready": False,
        "voice_handoff_at": None,
        "messages": [],
        "office": OFFICE,
    }
    return sid


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    s = _sessions.get(session_id)
    return deepcopy(s) if s else None


def update_session(session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    if session_id not in _sessions:
        raise KeyError("session not found")
    base = _sessions[session_id]
    for k, v in updates.items():
        if k == "patient" and isinstance(v, dict):
            base["patient"] = {**base["patient"], **v}
        elif k == "refill" and isinstance(v, dict):
            base["refill"] = {**base["refill"], **v}
        else:
            base[k] = v
    return deepcopy(base)


def replace_session(session_id: str, state: dict[str, Any]) -> None:
    _sessions[session_id] = deepcopy(state)


def append_message(session_id: str, role: str, content: str) -> None:
    if session_id not in _sessions:
        return
    _sessions[session_id]["messages"].append({"role": role, "content": content})
