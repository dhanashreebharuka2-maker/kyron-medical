"use client";

import { motion } from "framer-motion";
import type { Booking, SessionState } from "@/types/session";

type Props = { session: SessionState };

function fmt(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function AppointmentSummaryCard({ session }: Props) {
  const booking = session.booking as Booking | null;
  const confirmed = session.booking_confirmed && booking;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-slate-200/80 bg-white/60 p-4 shadow-sm backdrop-blur-xl"
    >
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Session</p>
      {confirmed ? (
        <div className="mt-2 space-y-1 text-sm">
          <p className="font-medium text-emerald-800">Appointment confirmed</p>
          <p className="text-slate-700">{booking.provider_name}</p>
          <p className="text-xs text-slate-600">{fmt(booking.start_iso)}</p>
        </div>
      ) : session.intake_complete && session.matched_provider_id ? (
        <p className="mt-2 text-sm text-slate-700">Intake complete — choose a time in the chat when slots appear.</p>
      ) : session.workflow === "scheduling" && !session.intake_complete ? (
        <p className="mt-2 text-sm text-slate-700">Scheduling — complete intake in the chat to see providers and times.</p>
      ) : session.workflow === "refill" ? (
        <p className="mt-2 text-sm text-slate-700">
          {session.refill_complete ? "Refill request recorded." : "Refill flow — use the chat to finish your request."}
        </p>
      ) : (
        <p className="mt-2 text-sm text-slate-700">Ask the assistant to book, refill, or share office details.</p>
      )}
    </motion.div>
  );
}
