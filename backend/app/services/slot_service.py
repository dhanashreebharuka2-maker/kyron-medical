"""Filter mock slots by provider and natural-language constraints."""
from __future__ import annotations


import re
from calendar import month_name
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.data.slot_generator import ALL_MOCK_SLOTS


def slots_for_provider(provider_id: str) -> List[Dict[str, Any]]:
    return [s for s in ALL_MOCK_SLOTS if s["provider_id"] == provider_id]


def _start_dt(slot: Dict[str, Any]) -> datetime:
    return datetime.fromisoformat(slot["start_iso"])


def filter_slots(
    slots: List[Dict[str, Any]],
    query: Optional[str],
    max_results: int = 12,
) -> List[Dict[str, Any]]:
    """Apply NL filters: morning, weekday names, today/tomorrow, ranges, earliest, etc."""
    if not query:
        return slots[:max_results]

    q = query.lower().strip()
    now = datetime.now()
    today = now.date()
    filtered = list(slots)

    def keep(predicate) -> None:
        nonlocal filtered
        filtered = [s for s in filtered if predicate(s)]

    # --- Time of day ---
    if "morning" in q or "before noon" in q or "a.m" in q or "am " in q:
        keep(lambda s: _start_dt(s).hour < 12)

    if "afternoon" in q or "after noon" in q:
        keep(lambda s: _start_dt(s).hour >= 12)

    if "evening" in q or "late day" in q:
        keep(lambda s: _start_dt(s).hour >= 16)

    if re.search(r"after\s*3|after\s*three|3\s*pm|3pm", q):
        keep(lambda s: _start_dt(s).hour >= 15)

    if re.search(r"before\s*11|before\s*eleven|10\s*am|10am", q):
        keep(lambda s: _start_dt(s).hour < 11)

    if re.search(r"between\s*10\s*(and|:|-|to)\s*2|10\s*(-|to)\s*2\s*pm", q):
        keep(lambda s: 10 <= _start_dt(s).hour < 14)

    # --- Weekdays ---
    if "tuesday" in q or "tues" in q:
        keep(lambda s: _start_dt(s).weekday() == 1)
    if "monday" in q:
        keep(lambda s: _start_dt(s).weekday() == 0)
    if "wednesday" in q or "wed" in q:
        keep(lambda s: _start_dt(s).weekday() == 2)
    if "thursday" in q or "thurs" in q:
        keep(lambda s: _start_dt(s).weekday() == 3)
    if "friday" in q:
        keep(lambda s: _start_dt(s).weekday() == 4)
    if "weekday" in q or "week day" in q:
        keep(lambda s: _start_dt(s).weekday() < 5)
    if "weekend" in q:
        keep(lambda s: _start_dt(s).weekday() >= 5)

    # --- Relative dates ---
    if "today" in q:
        keep(lambda s: _start_dt(s).date() == today)

    if "tomorrow" in q:
        keep(lambda s: _start_dt(s).date() == today + timedelta(days=1))

    if "this week" in q:
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        keep(lambda s: start <= _start_dt(s).date() < end)

    if "next week" in q:
        start = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
        end = start + timedelta(days=7)
        keep(lambda s: start <= _start_dt(s).date() < end)

    # Month names (e.g. "in March")
    for i, name in enumerate(month_name):
        if i == 0:
            continue
        if name.lower() in q:
            mnum = i
            keep(lambda s, m=mnum: _start_dt(s).month == m)
            break

    # --- Sort / preference ---
    if "sooner" in q or "earliest" in q or "soon" in q or "asap" in q or "next available" in q:
        filtered = sorted(filtered, key=lambda s: s["start_iso"])[:max_results]
        return filtered

    filtered = sorted(filtered, key=lambda s: s["start_iso"])
    return filtered[:max_results]
