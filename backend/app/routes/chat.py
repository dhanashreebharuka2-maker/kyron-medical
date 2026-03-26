from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse, SessionStateResponse
from app.schemas.patient import PatientIntakeBody, RefillRequestBody, SlotQueryBody
from app.services.chat_orchestrator import process_chat
from app.services.session_logic import apply_session_updates, recompute_derived
from app.services.session_service import append_message, get_session, new_session, replace_session

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/session", response_model=SessionStateResponse)
def create_session():
    sid = new_session()
    s = get_session(sid)
    if not s:
        raise HTTPException(500, "session creation failed")
    return SessionStateResponse(session_id=sid, session=s)


@router.get("/session/{session_id}", response_model=SessionStateResponse)
def read_session(session_id: str):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "session not found")
    return SessionStateResponse(session_id=session_id, session=s)


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    sid = body.session_id
    if not sid:
        sid = new_session()
    elif get_session(sid) is None:
        raise HTTPException(404, "session not found")

    try:
        msg, session, ui_hints = process_chat(sid, body.message)
    except ValueError:
        raise HTTPException(404, "session not found")

    return ChatResponse(session_id=sid, assistant_message=msg, session=session, ui_hints=ui_hints)


@router.post("/session/{session_id}/intake", response_model=SessionStateResponse)
def submit_intake(session_id: str, body: PatientIntakeBody):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "session not found")

    updates = {
        "workflow": "scheduling",
        "patient": {
            "first_name": body.first_name.strip(),
            "last_name": body.last_name.strip(),
            "dob": body.dob.strip(),
            "phone": body.phone.strip(),
            "email": body.email.strip(),
        },
        "reason_for_visit": body.reason_for_visit.strip(),
        "intake_complete": True,
    }
    apply_session_updates(s, updates)
    recompute_derived(s)
    replace_session(session_id, s)
    append_message(
        session_id,
        "assistant",
        "Thanks — I've saved your information. I'll show matching providers and available times next.",
    )
    out = get_session(session_id)
    if not out:
        raise HTTPException(500, "session update failed")
    return SessionStateResponse(session_id=session_id, session=out)


@router.post("/session/{session_id}/refill", response_model=SessionStateResponse)
def submit_refill(session_id: str, body: RefillRequestBody):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "session not found")

    apply_session_updates(
        s,
        {
            "workflow": "refill",
            "refill": {
                "medication": body.medication.strip(),
                "notes": (body.notes or "").strip(),
                "pharmacy": (body.pharmacy or "").strip() or None,
                "urgency": (body.urgency or "routine").strip() or "routine",
            },
            "refill_complete": True,
        },
    )
    recompute_derived(s)
    replace_session(session_id, s)
    notes = (body.notes or "").strip()
    pharm = (body.pharmacy or "").strip()
    urg = (body.urgency or "routine").strip()
    extra = []
    if pharm:
        extra.append(f"Pharmacy noted: {pharm}.")
    if urg and urg != "routine":
        extra.append(f"Priority: {urg}.")
    tail = " ".join(extra)
    append_message(
        session_id,
        "assistant",
        f"Thanks — I've recorded your refill request for {body.medication.strip()}. {tail} Our team will review it; "
        "this assistant cannot approve medications. For urgent needs, call the office.",
    )
    out = get_session(session_id)
    if not out:
        raise HTTPException(500, "session update failed")
    return SessionStateResponse(session_id=session_id, session=out)


@router.post("/session/{session_id}/slot-query", response_model=SessionStateResponse)
def update_slot_query(session_id: str, body: SlotQueryBody):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "session not found")
    apply_session_updates(s, {"slot_query": body.query})
    recompute_derived(s)
    replace_session(session_id, s)
    out = get_session(session_id)
    if not out:
        raise HTTPException(500, "session update failed")
    return SessionStateResponse(session_id=session_id, session=out)
