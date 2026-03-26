from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BookingRequest(BaseModel):
    session_id: str
    slot_id: str = Field(..., min_length=1)


class BookingResponse(BaseModel):
    success: bool
    message: str
    booking: Optional[Dict[str, Any]] = None
    session: Dict[str, Any]
    email_mock: bool = False
    sms_mock: bool = False
