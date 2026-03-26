from __future__ import annotations

from fastapi import APIRouter

from app.data.providers import PROVIDERS
from app.schemas.providers import ProviderOut

router = APIRouter(prefix="/api", tags=["providers"])


@router.get("/providers", response_model=list[ProviderOut])
def list_providers():
    return [ProviderOut(**p) for p in PROVIDERS]
