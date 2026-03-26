"""Shared httpx settings for outbound HTTPS (TLS 1.2+, modern CA bundle)."""
from __future__ import annotations

import ssl
from typing import Any

import certifi
import httpx


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=certifi.where())
    if hasattr(ssl, "TLSVersion"):
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def async_httpx_client(*, timeout: float = 45.0, **kwargs: Any) -> httpx.AsyncClient:
    """
    AsyncClient tuned for APIs that reject legacy TLS (e.g. Bland).
    http2=False avoids optional h2 stack quirks on some macOS/Python builds.
    """
    kwargs.setdefault("http2", False)
    # Avoid unexpected HTTPS proxies from environment variables (HTTP(S)_PROXY),
    # which can break calls to third-party APIs in local dev.
    kwargs.setdefault("trust_env", False)
    return httpx.AsyncClient(timeout=timeout, verify=_ssl_context(), **kwargs)
