from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional


def parse_dob(text: str) -> Optional[str]:
    """Normalize DOB to YYYY-MM-DD if parseable."""
    t = text.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y"):
        try:
            d = datetime.strptime(t, fmt).date()
            if d > date.today():
                return None
            return d.isoformat()
        except ValueError:
            continue
    return None


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email.strip()))


def normalize_phone(phone: str) -> Optional[str]:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return digits
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return None


def is_medical_advice_request(text: str) -> bool:
    """Lightweight flag for obvious clinical advice patterns (guardrails also in system prompt)."""
    lower = text.lower()
    bad = [
        "diagnos",
        "what should i take",
        "prescribe",
        "dosage",
        "is it cancer",
        "should i stop taking",
        "interpret my lab",
        "read my x-ray",
    ]
    return any(b in lower for b in bad)
