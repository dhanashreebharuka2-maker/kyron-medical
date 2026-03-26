"""Infer voice booking from call transcripts (Bland webhook or GET /v1/calls/{id}); reuse web booking + email path."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_WORD_ORD = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
}


def _looks_like_uuid(s: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", s, re.I))


def _deep_find_call_id(obj: Any, depth: int = 0) -> Optional[str]:
    if depth > 12 or not isinstance(obj, dict):
        return None
    for k, v in obj.items():
        if k in ("callId", "call_id", "c_id") and isinstance(v, str) and (v.strip() and _looks_like_uuid(v.strip())):
            return v.strip()
        if k == "id" and isinstance(v, str) and _looks_like_uuid(v):
            parent_type = str(obj.get("type") or "")
            if "call" in parent_type.lower() or "conversation" in parent_type.lower():
                return v
    for v in obj.values():
        if isinstance(v, dict):
            got = _deep_find_call_id(v, depth + 1)
            if got:
                return got
        elif isinstance(v, list):
            for item in v[:30]:
                if isinstance(item, dict):
                    got = _deep_find_call_id(item, depth + 1)
                    if got:
                        return got
    return None


def _join_message_list(messages: List[Any]) -> str:
    lines: List[str] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or m.get("speaker") or "?")
        if role == "system":
            continue  # skip system prompt — only user/assistant turns matter for inference
        # Vapi artifact uses "message" key; OpenAI format uses "content"
        content = m.get("content") or m.get("message")
        if isinstance(content, str) and content.strip():
            lines.append(f"{role}: {content.strip()}")
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    t = part.get("text") or ""
                    if isinstance(t, str) and t.strip():
                        lines.append(f"{role}: {t.strip()}")
    return "\n".join(lines)


def _transcript_from_artifact(art: Any) -> str:
    if not isinstance(art, dict):
        return ""
    for key in ("transcript", "combinedTranscript", "combined_transcript"):
        raw = art.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    for key in ("messages", "messagesOpenAI", "openaiMessages", "openai_messages"):
        raw = art.get(key)
        if isinstance(raw, list) and raw:
            joined = _join_message_list(raw)
            if joined.strip():
                return joined.strip()
    return ""


def extract_transcript_from_voice_blob(blob: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Transcript + optional call id from Bland post-call webhook or GET /v1/calls/{id}.
    Also supports legacy nested shapes (Vapi-style) for old integrations.
    """
    if not isinstance(blob, dict):
        return "", None

    call_id: Optional[str] = None
    for k in ("call_id", "c_id"):
        v = blob.get(k)
        if isinstance(v, str) and v.strip():
            call_id = v.strip()
            break

    # Bland: full transcript string
    ct = blob.get("concatenated_transcript")
    if isinstance(ct, str) and ct.strip():
        return ct.strip(), call_id

    # Bland: phrase list
    ts = blob.get("transcripts")
    if isinstance(ts, list) and ts:
        lines: List[str] = []
        for m in ts:
            if isinstance(m, dict) and isinstance(m.get("text"), str) and m["text"].strip():
                u = str(m.get("user") or "?")
                lines.append(f"{u}: {m['text'].strip()}")
        if lines:
            return "\n".join(lines), call_id

    # Direct fields
    for key in ("transcript", "combinedTranscript"):
        v = blob.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip(), call_id

    # Legacy nested (Vapi envelope)
    msg = blob.get("message")
    if isinstance(msg, dict):
        if not call_id:
            call_id = _deep_find_call_id(msg) or call_id
        art = msg.get("artifact")
        t = _transcript_from_artifact(art)
        if t:
            return t, call_id
        inner = msg.get("call")
        if isinstance(inner, dict):
            t2, _ = extract_transcript_from_voice_blob(inner)
            if t2:
                return t2, call_id or inner.get("id") if isinstance(inner.get("id"), str) else call_id

    art = blob.get("artifact")
    t = _transcript_from_artifact(art)
    if t:
        return t, call_id

    for key in ("messages", "artifact"):
        sub = blob.get(key)
        if isinstance(sub, dict):
            t = _transcript_from_artifact(sub)
            if t:
                return t, call_id

    raw = blob.get("messages")
    if isinstance(raw, list) and raw:
        joined = _join_message_list(raw)
        if joined.strip():
            return joined.strip(), call_id

    if not call_id:
        call_id = _deep_find_call_id(blob)
    return "", call_id


async def resolve_transcript_text(payload: Dict[str, Any]) -> str:
    """Transcript from webhook payload (Vapi/Bland/etc.)."""
    text, call_id = extract_transcript_from_voice_blob(payload)
    if text.strip():
        return text.strip()
    return ""


def _ordinal_heuristic(transcript: str) -> Optional[int]:
    """Last-resort: pick up explicit option numbers from the tail of the transcript."""
    lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
    tail = "\n".join(lines[-16:]).lower()
    for pat in (
        r"(?:option|number|#|pick)\s*(\d)",
        r"\b(\d)\s*(?:works|is good|sounds good|please|thanks|yes)\b",
        r"\b(?:i'?ll take|i want|book|choose|pick)\s+(?:option|number)?\s*#?\s*(\d)\b",
    ):
        m = re.search(pat, tail, re.I)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 12:
                return n
    wm = re.search(
        r"\b(first|second|third|fourth|fifth)\s+(?:option|one|choice|slot|time)\b",
        tail,
        re.I,
    )
    if wm:
        return _WORD_ORD.get(wm.group(1).lower())
    return None


def _ordinal_openai(transcript: str, offered_slots: List[Dict[str, Any]]) -> Optional[int]:
    if not settings.openai_api_key or not offered_slots:
        return None
    opts = [
        {"ordinal": o.get("ordinal"), "label_voice": o.get("label_voice"), "id": o.get("id")}
        for o in offered_slots
        if isinstance(o, dict) and o.get("ordinal") is not None
    ]
    if not opts:
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    schema = """
Return a single JSON object only:
{
  "slot_ordinal": <integer 1-8 or null>,
  "confidence": "high"|"medium"|"low"
}
Rules:
- The patient was offered numbered appointment options (1, 2, 3...) for Kyron Medical scheduling.
- Set slot_ordinal only if the caller clearly confirms one of those options by number or unambiguous phrase
  (e.g. "the first one", "option 2").
- If they decline, are unclear, or discuss something other than picking a listed time, use null.
""".strip()
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": schema},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"offered_options": opts, "call_transcript": transcript[:24000]},
                        default=str,
                    ),
                },
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        n = data.get("slot_ordinal")
        conf = (data.get("confidence") or "").lower()
        if conf == "low":
            return None
        if isinstance(n, int) and 1 <= n <= 24:
            return n
    except Exception:
        logger.exception("OpenAI transcript slot inference failed")
    return None


def infer_slot_ordinal_from_transcript(
    transcript: str,
    offered_slots: List[Dict[str, Any]],
) -> Optional[int]:
    """
    Map a call transcript + the session's voice_offered_slots list to a 1-based ordinal, or None.
    """
    if not transcript or not transcript.strip():
        return None
    valid = {int(o["ordinal"]) for o in offered_slots if isinstance(o, dict) and o.get("ordinal") is not None}
    if not valid:
        return None

    h = _ordinal_heuristic(transcript)
    if h is not None and h in valid:
        return h

    ai = _ordinal_openai(transcript, offered_slots)
    if ai is not None and ai in valid:
        return ai

    return None
