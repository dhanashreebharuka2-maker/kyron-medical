"""Semantic-ish provider matching from free-text reason for visit."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from app.data.providers import PROVIDERS, SPECIALTY_KEYWORDS


def match_provider_from_reason(reason: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Returns (provider_dict, None) on match, or (None, explanation) if no match / unsupported.
    """
    if not reason or not reason.strip():
        return None, "No reason for visit was provided yet."

    r = reason.lower()
    scores: dict[str, int] = {p["id"]: 0 for p in PROVIDERS}

    for pid, keywords in SPECIALTY_KEYWORDS.items():
        for kw in keywords:
            if kw in r:
                scores[pid] += 2
            # word boundary-ish: first 4 chars
            if len(kw) >= 4 and kw[:4] in r:
                scores[pid] += 1

    best_id = max(scores, key=lambda k: scores[k])
    best_score = scores[best_id]

    if best_score == 0:
        return (
            None,
            "We could not confidently match that concern to one of our in-network specialties. "
            "Please describe symptoms in plain language (e.g., skin rash, knee pain) or ask for our office phone.",
        )

    prov = next(p for p in PROVIDERS if p["id"] == best_id)
    return prov, None


def get_provider_by_id(provider_id: str) -> Optional[Dict[str, Any]]:
    for p in PROVIDERS:
        if p["id"] == provider_id:
            return p
    return None
