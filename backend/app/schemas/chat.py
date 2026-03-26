from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    session: Dict[str, Any]
    ui_hints: Dict[str, Any] = Field(default_factory=dict)


class SessionStateResponse(BaseModel):
    session_id: str
    session: Dict[str, Any]
