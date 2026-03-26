from __future__ import annotations

from pydantic import BaseModel


class ProviderOut(BaseModel):
    id: str
    full_name: str
    specialty: str
    body_part_focus: str
    description: str


class SlotOut(BaseModel):
    id: str
    provider_id: str
    start_iso: str
    end_iso: str
    duration_minutes: int
