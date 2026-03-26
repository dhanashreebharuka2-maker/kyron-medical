from __future__ import annotations

import re
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: Optional[str] = None
    cors_origins: str = "http://localhost:3000"
    resend_api_key: Optional[str] = None
    email_from: str = "Kyron Medical <appointments@example.com>"
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    # SMS: auto = TEXTBELT_API_KEY if set, else Twilio if fully configured, else mock
    sms_provider: str = "auto"
    textbelt_api_key: Optional[str] = None

    # Voice outbound — Vapi (https://vapi.ai). Demo handoff if any required key is missing.
    vapi_api_key: Optional[str] = None
    vapi_assistant_id: Optional[str] = None
    vapi_phone_number_id: Optional[str] = None
    # Optional reference only — outbound calls do not send this; set the webhook URL on the assistant in Vapi.
    vapi_webhook_url: Optional[str] = None

    @field_validator("twilio_from_number", mode="before")
    @classmethod
    def strip_twilio_from_e164(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        return re.sub(r"\s+", "", s)

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
