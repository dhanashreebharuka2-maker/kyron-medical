from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    session_id: str


class SmsOptInRequest(BaseModel):
    session_id: str
    opt_in: bool = Field(..., description="User must explicitly opt in")


class SmsSendResponse(BaseModel):
    success: bool
    message: str
    mock: bool
    session: Dict[str, Any]
