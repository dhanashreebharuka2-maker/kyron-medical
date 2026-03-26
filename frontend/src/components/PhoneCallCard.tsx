"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { readSession, voiceHandoff, createSession } from "@/lib/api";
import type { SessionState } from "@/types/session";

type Props = {
  /** Pass the current chat session so booking shows on the same session. */
  sessionId?: string | null;
  onSessionUpdate?: (s: SessionState) => void;
};

function formatPhoneDisplay(raw: string): string {
  const d = raw.replace(/\D/g, "").slice(0, 10);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `(${d.slice(0, 3)}) ${d.slice(3)}`;
  return `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}`;
}

function isValidPhone(raw: string): boolean {
  const d = raw.replace(/\D/g, "");
  return d.length === 10 || (d.length === 11 && d.startsWith("1"));
}

type CallState = "idle" | "calling" | "ringing" | "booking" | "confirmed" | "error";

export function PhoneCallCard({ sessionId, onSessionUpdate }: Props) {
  const [phone, setPhone] = useState("");
  const [callState, setCallState] = useState<CallState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState<SessionState["booking"] | null>(null);
  const [smsSent, setSmsSent] = useState(false);
  const activeSessionId = useRef<string | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const valid = isValidPhone(phone);

  // Poll the session for booking confirmation after call is placed
  useEffect(() => {
    if (callState !== "ringing" && callState !== "booking") {
      if (pollTimer.current) clearInterval(pollTimer.current);
      return;
    }
    let attempts = 0;
    const maxAttempts = 72; // ~6 minutes

    const tick = async () => {
      if (!activeSessionId.current) return;
      attempts += 1;
      if (attempts > maxAttempts) {
        if (pollTimer.current) clearInterval(pollTimer.current);
        return;
      }
      try {
        const { session } = await readSession(activeSessionId.current);
        onSessionUpdate?.(session);
        if (session.booking_confirmed && session.booking) {
          setBooking(session.booking);
          setSmsSent(Boolean(session.sms_sent));
          setCallState("confirmed");
          if (pollTimer.current) clearInterval(pollTimer.current);
        } else if (attempts > 3) {
          setCallState("booking");
        }
      } catch {
        // ignore transient errors
      }
    };

    pollTimer.current = setInterval(() => void tick(), 5000);
    return () => { if (pollTimer.current) clearInterval(pollTimer.current); };
  }, [callState]);

  const handleCall = async () => {
    if (!valid || callState !== "idle") return;
    setCallState("calling");
    setError(null);
    try {
      // Use existing chat session if available — booking will show on same page session.
      // Fall back to fresh session for standalone use.
      let sid = sessionId;
      if (!sid) {
        const { session_id } = await createSession();
        sid = session_id;
      }
      activeSessionId.current = sid;
      await voiceHandoff(sid, phone);
      setCallState("ringing");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Call failed. Please try again.");
      setCallState("error");
    }
  };

  const reset = () => {
    setCallState("idle");
    setError(null);
    setBooking(null);
    setSmsSent(false);
    setPhone("");
    activeSessionId.current = null;
  };

  return (
    <div className="rounded-2xl border border-slate-200/70 bg-white/80 p-5 shadow-sm backdrop-blur-xl">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">Call me now</p>
          <p className="text-xs text-slate-500">Enter your number — Alex will call you</p>
        </div>
      </div>

      <AnimatePresence mode="wait">

        {/* CONFIRMED */}
        {callState === "confirmed" ? (
          <motion.div key="confirmed" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
            className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 space-y-2">
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 shrink-0 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <p className="text-sm font-semibold text-emerald-800">Appointment confirmed</p>
            </div>
            {booking && (
              <p className="text-xs text-emerald-700 ml-6">
                {booking.provider_name} — {new Date(booking.start_iso).toLocaleString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
              </p>
            )}
            <p className="text-xs text-emerald-700 ml-6">
              {smsSent ? "✓ Confirmation SMS sent to your phone." : "SMS will send once confirmed."}
            </p>
            <button type="button" onClick={reset}
              className="ml-6 mt-1 text-[11px] font-semibold text-emerald-700 underline underline-offset-2">
              Make another call
            </button>
          </motion.div>

        ) : callState === "ringing" || callState === "booking" ? (
          /* RINGING / WAITING */
          <motion.div key="ringing" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="rounded-xl border border-sky-200 bg-sky-50 p-4 space-y-2">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-sky-500" />
              </span>
              <p className="text-sm font-semibold text-sky-800">
                {callState === "ringing" ? "Calling you now — answer when it rings" : "Call in progress — booking your appointment…"}
              </p>
            </div>
            <p className="text-xs text-sky-700 ml-5">
              After you hang up, this card will update with your confirmed time and SMS status.
            </p>
          </motion.div>

        ) : callState === "error" ? (
          /* ERROR */
          <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <p className="text-xs text-red-600 rounded-xl border border-red-200 bg-red-50 px-3 py-2">{error}</p>
            <button type="button" onClick={reset}
              className="w-full rounded-xl border border-slate-200 py-2 text-sm text-slate-600 hover:bg-slate-50">
              Try again
            </button>
          </motion.div>

        ) : (
          /* IDLE FORM */
          <motion.div key="form" initial={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col gap-3">
            <input
              type="tel"
              inputMode="numeric"
              placeholder="(555) 867-5309"
              value={formatPhoneDisplay(phone)}
              onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
              onKeyDown={(e) => { if (e.key === "Enter") void handleCall(); }}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
            />
            <motion.button
              whileHover={{ scale: valid ? 1.02 : 1 }}
              whileTap={{ scale: valid ? 0.98 : 1 }}
              type="button"
              disabled={!valid || callState === "calling"}
              onClick={() => void handleCall()}
              className="w-full rounded-xl bg-gradient-to-b from-slate-800 to-slate-900 py-2.5 text-sm font-semibold text-white shadow-md shadow-slate-900/20 ring-1 ring-white/10 hover:from-slate-700 hover:to-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {callState === "calling" ? "Calling…" : "Call me"}
            </motion.button>
            <p className="text-center text-[11px] text-slate-400">
              Or <span className="font-medium text-slate-600">chat below</span> to schedule, refill, or get office info
            </p>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
