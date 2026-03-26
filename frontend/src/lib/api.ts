import type { Booking, SessionState } from "@/types/session";

const base = ""; // same-origin; Next.js rewrites to FastAPI

export type BookingApiResponse = {
  success: boolean;
  message: string;
  booking: Booking | null;
  session: SessionState;
  email_mock?: boolean;
  sms_mock?: boolean;
};

export type SmsOptInApiResponse = {
  success: boolean;
  message: string;
  mock: boolean;
  session: SessionState;
};

export type VoiceHandoffApiResponse = {
  success: boolean;
  message: string;
  handoff_payload?: Record<string, unknown>;
  voice_context_summary?: string;
  structured_context?: Record<string, unknown>;
  continuation_prompt?: string;
  demo_mode?: boolean;
  voice_call_placed?: boolean;
  voice_call_id?: string | null;
  voice_error?: string | null;
  session: SessionState;
};

export type VoiceBlandSyncApiResponse = {
  success: boolean;
  pending?: boolean;
  message?: string;
  session?: SessionState;
  booking?: unknown;
  kyron_hint?: string;
};

export async function createSession(signal?: AbortSignal): Promise<{ session_id: string; session: SessionState }> {
  const r = await fetch(`${base}/api/session`, { method: "POST", signal });
  if (!r.ok) throw new Error("Failed to create session");
  return (await r.json()) as { session_id: string; session: SessionState };
}

export async function readSession(
  sessionId: string,
  signal?: AbortSignal
): Promise<{ session_id: string; session: SessionState }> {
  const r = await fetch(`${base}/api/session/${sessionId}`, { method: "GET", signal });
  if (!r.ok) throw new Error("Failed to load session");
  return (await r.json()) as { session_id: string; session: SessionState };
}

export async function sendChat(
  sessionId: string | null,
  message: string
): Promise<{
  session_id: string;
  assistant_message: string;
  session: SessionState;
  ui_hints: Record<string, unknown>;
}> {
  const r = await fetch(`${base}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!r.ok) throw new Error("Chat failed");
  return (await r.json()) as {
    session_id: string;
    assistant_message: string;
    session: SessionState;
    ui_hints: Record<string, unknown>;
  };
}

export async function submitRefill(
  sessionId: string,
  body: { medication: string; notes?: string; pharmacy?: string; urgency?: string }
): Promise<{ session: SessionState }> {
  const r = await fetch(`${base}/api/session/${sessionId}/refill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      medication: body.medication,
      notes: body.notes ?? "",
      pharmacy: body.pharmacy ?? "",
      urgency: body.urgency ?? "routine",
    }),
  });
  if (!r.ok) throw new Error("Refill submit failed");
  return (await r.json()) as { session: SessionState };
}

export async function submitIntake(
  sessionId: string,
  body: {
    first_name: string;
    last_name: string;
    dob: string;
    phone: string;
    email: string;
    reason_for_visit: string;
  }
): Promise<{ session: SessionState }> {
  const r = await fetch(`${base}/api/session/${sessionId}/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error("Intake failed");
  return (await r.json()) as { session: SessionState };
}

export async function slotQuery(sessionId: string, query: string): Promise<{ session: SessionState }> {
  const r = await fetch(`${base}/api/session/${sessionId}/slot-query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!r.ok) throw new Error("Filter failed");
  return (await r.json()) as { session: SessionState };
}

export async function bookSlot(sessionId: string, slotId: string): Promise<BookingApiResponse> {
  const r = await fetch(`${base}/api/book`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, slot_id: slotId }),
  });
  if (!r.ok) throw new Error("Booking failed");
  return (await r.json()) as BookingApiResponse;
}

export async function smsOptIn(sessionId: string, optIn: boolean): Promise<SmsOptInApiResponse> {
  const r = await fetch(`${base}/api/notify/sms-opt-in`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, opt_in: optIn }),
  });
  if (!r.ok) throw new Error("SMS opt-in failed");
  return (await r.json()) as SmsOptInApiResponse;
}

export async function voiceHandoff(sessionId: string, phoneOverride?: string): Promise<VoiceHandoffApiResponse> {
  const r = await fetch(`${base}/api/voice/handoff`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, patient_phone_override: phoneOverride || null }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Voice handoff failed");
  }
  return (await r.json()) as VoiceHandoffApiResponse;
}

/** Create a fresh session and immediately place a call — used by the standalone PhoneCallCard. */
export async function directVoiceCall(phone: string): Promise<VoiceHandoffApiResponse> {
  const { session_id } = await createSession();
  return voiceHandoff(session_id, phone);
}

export async function voiceBlandSync(
  sessionId: string,
  callId?: string | null
): Promise<VoiceBlandSyncApiResponse> {
  const r = await fetch(`${base}/api/voice/bland-sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, call_id: callId ?? null }),
  });
  if (!r.ok) throw new Error("Voice sync failed");
  return (await r.json()) as VoiceBlandSyncApiResponse;
}
