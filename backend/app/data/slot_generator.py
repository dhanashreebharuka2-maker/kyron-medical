"""Generate mock appointment slots for the next ~45 weekdays."""
from __future__ import annotations


from datetime import date, datetime, timedelta
from typing import Any

from app.data.providers import PROVIDERS


def _weekday_dates(start: date, num_days: int) -> list[date]:
    out: list[date] = []
    d = start
    end = start + timedelta(days=num_days)
    while d < end:
        if d.weekday() < 5:  # Mon–Fri
            out.append(d)
        d += timedelta(days=1)
    return out


def _slot_times() -> list[tuple[int, int]]:
    """30-minute slots 9:00–16:30."""
    slots: list[tuple[int, int]] = []
    for h in range(9, 17):
        for m in (0, 30):
            if h == 16 and m == 30:
                break
            slots.append((h, m))
    return slots


def build_all_slots(days_ahead: int = 60) -> list[dict[str, Any]]:
    """Deterministic mock slots: each doctor gets a subset of weekday slots."""
    today = date.today()
    dates = _weekday_dates(today, days_ahead)
    slot_times = _slot_times()
    all_slots: list[dict[str, Any]] = []
    idx = 0
    for prov in PROVIDERS:
        pid = prov["id"]
        # Stagger which slots each provider offers so lists differ
        offset = hash(pid) % 5
        for d in dates:
            for ti, (hh, mm) in enumerate(slot_times):
                if (ti + offset) % 3 != 0:
                    continue  # sparse availability
                start_dt = datetime(d.year, d.month, d.day, hh, mm)
                end_dt = start_dt + timedelta(minutes=30)
                slot_id = f"{pid}-{start_dt.isoformat()}"
                all_slots.append(
                    {
                        "id": slot_id,
                        "provider_id": pid,
                        "start_iso": start_dt.isoformat(),
                        "end_iso": end_dt.isoformat(),
                        "duration_minutes": 30,
                    }
                )
                idx += 1
    return sorted(all_slots, key=lambda s: s["start_iso"])


# Cached at import for MVP (restart server to refresh dates)
ALL_MOCK_SLOTS: list[dict[str, Any]] = build_all_slots(60)
