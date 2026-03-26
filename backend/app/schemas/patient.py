from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class PatientIntakeBody(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    dob: str = Field(..., min_length=8, max_length=32)
    phone: str = Field(..., min_length=10, max_length=32)
    email: EmailStr
    reason_for_visit: str = Field(..., min_length=3, max_length=2000)


class SlotQueryBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class RefillRequestBody(BaseModel):
    medication: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=2000)
    pharmacy: str = Field(default="", max_length=200)
    urgency: str = Field(default="routine", max_length=32)
