"""Thin OpenAI wrapper for JSON-mode orchestration."""
from __future__ import annotations


import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.config import settings
from app.utils.guardrails import SYSTEM_SAFETY_PREAMBLE


def run_json_orchestration(
    session: Dict[str, Any],
    user_message: str,
    recent_messages: List[Dict[str, str]],
) -> Optional[Dict[str, Any]]:
    """
    Returns parsed dict with keys assistant_message, session_updates (optional), or None on failure.
    """
    if not settings.openai_api_key:
        return None

    client = OpenAI(api_key=settings.openai_api_key)

    schema_hint = """
Respond with a single JSON object (no markdown) with this shape:
{
  "assistant_message": "string — what the patient sees next",
  "session_updates": {
    "workflow": "scheduling" | "refill" | "office" | "general" | null,
    "patient": { "first_name": "...", "last_name": "...", "dob": "...", "phone": "...", "email": "..." },
    "reason_for_visit": "string or null",
    "slot_query": "string or null — natural language filter for slots",
    "selected_slot_id": "string or null",
    "intake_complete": true/false or omit,
    "refill": { "medication": "...", "notes": "...", "pharmacy": "...", "urgency": "routine|soon|urgent" },
    "sms_opt_in": true/false or null
  }
}
Rules:
- assistant_message must directly address the user's LAST message. Do not repeat the same long welcome you already gave
  earlier in the thread unless the user asks again.
- If they ask to book or schedule, acknowledge that and tell them you’ll collect intake details in the chat (step by
  step) — do not re-send the generic "what would you like to do" opener.
- If they mention prescription refill, medication, pharmacy, or "refill", set session_updates.workflow to "refill" and
  tell them to use the refill flow in the chat (do not give medical advice).
- If workflow is already "refill" and the user names a medication or strength (e.g. "Ibuprofen 800mg", "Lisinopril"),
  set session_updates.refill.medication to that text, session_updates.refill_complete to true, and confirm — do not
  repeat "What medication are you asking about?"
- Only include keys in session_updates that changed.
For scheduling: collect intake first, then reason_for_visit, then help refine slot_query.
Do not set booking_confirmed here — booking is confirmed via UI or explicit booking endpoint.
""".strip()

    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent_messages[-12:])

    system = f"""{SYSTEM_SAFETY_PREAMBLE}

You are Alex, Kyron Medical's administrative chat assistant (scheduling, refill routing, office info only — not medical advice). Address the patient in that voice.

{schema_hint}

Current session (JSON):
{json.dumps(session, default=str)}

Conversation tail:
{history_text}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        return None
