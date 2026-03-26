"""Kyron Medical — FastAPI entrypoint."""
from __future__ import annotations


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.routes.booking import router as booking_router
from app.routes.chat import router as chat_router
from app.routes.notifications import router as notifications_router
from app.routes.providers import router as providers_router
from app.routes.voice import router as voice_router

app = FastAPI(title="Kyron Medical API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(providers_router)
app.include_router(booking_router)
app.include_router(notifications_router)
app.include_router(voice_router)


@app.get("/")
def root():
    """Opening http://127.0.0.1:8000/ in a browser goes to interactive API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/twilio")
def twilio_health():
    """Non-secret check that Twilio env vars are loaded (restart API after editing .env)."""
    c = bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from_number
    )
    return {
        "twilio_env_configured": c,
        "from_number_last4": settings.twilio_from_number[-4:] if settings.twilio_from_number else None,
        "account_sid_last4": settings.twilio_account_sid[-4:] if settings.twilio_account_sid else None,
    }


@app.get("/health/sms")
def sms_health():
    """Which SMS backend will send (Textbelt vs Twilio vs mock). Restart after .env changes."""
    from app.services.sms_service import resolve_active_sms_provider

    p = resolve_active_sms_provider()
    tb = bool((settings.textbelt_api_key or "").strip())
    tw = bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from_number
    )
    return {
        "active_provider": p,
        "sms_provider_setting": settings.sms_provider,
        "textbelt_key_configured": tb,
        "twilio_env_configured": tw,
    }
