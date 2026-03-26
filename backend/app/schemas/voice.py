from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VoiceHandoffRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    patient_phone_override: Optional[str] = None


class VoiceChooseSlotRequest(BaseModel):
    """Record which offered slot the caller chose (by option number)."""

    session_id: str = Field(..., min_length=1)
    slot_ordinal: int = Field(..., ge=1, le=24)


class VoiceBlandSyncRequest(BaseModel):
    """Poll Bland GET /v1/calls/{id} after a handoff when no webhook is configured."""

    session_id: str = Field(..., min_length=1)
    call_id: Optional[str] = None


class VoiceVapiWebhookPayload(BaseModel):
    """Vapi webhook payload (kept loose; Vapi shapes vary by plan/version)."""

    payload: Dict[str, Any]


class VoiceHandoffResponse(BaseModel):
    success: bool
    message: str
    handoff_payload: Dict[str, Any]
    voice_context_summary: str
    structured_context: Dict[str, Any]
    continuation_prompt: str
    demo_mode: bool
    voice_call_placed: bool
    voice_call_id: Optional[str] = None
    voice_error: Optional[str] = None
    session: Dict[str, Any]
