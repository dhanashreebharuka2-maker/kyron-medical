"use client";

import { motion } from "framer-motion";
import type { Booking } from "@/types/session";

type Props = {
  booking: Booking;
  emailSent: boolean;
  emailMock?: boolean;
  smsOptIn: boolean | null;
  smsSent: boolean;
  smsMock?: boolean;
  smsLastError?: string | null;
  smsMessageSid?: string | null;
  onSmsChoice: (optIn: boolean) => Promise<void>;
  embedded?: boolean;
};

function fmt(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function BookingConfirmationCard({
  booking,
  emailSent,
  emailMock,
  smsOptIn,
  smsSent,
  smsMock,
  smsLastError,
  smsMessageSid,
  onSmsChoice,
  embedded,
}: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className={
        embedded
          ? "rounded-2xl border border-emerald-200/80 bg-emerald-50/95 p-4 shadow-inner backdrop-blur-xl"
          : "rounded-2xl border border-emerald-200/80 bg-emerald-50/90 p-6 shadow-glass-lg backdrop-blur-2xl"
      }
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Confirmed</p>
      <h3
        className={`mt-1 font-display font-semibold text-ink ${embedded ? "text-xl sm:text-2xl" : "text-2xl"}`}
      >
        You&apos;re booked
      </h3>
      <dl className="mt-4 space-y-2 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Provider</dt>
          <dd className="text-right font-medium text-ink">{booking.provider_name}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Specialty</dt>
          <dd className="text-right text-ink">{booking.specialty}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">When</dt>
          <dd className="text-right text-ink">{fmt(booking.start_iso)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Office</dt>
          <dd className="max-w-[60%] text-right text-ink">{booking.office_name}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Address</dt>
          <dd className="max-w-[60%] text-right text-sm text-slate-700">{booking.office_address}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Phone</dt>
          <dd className="text-right text-ink">{booking.office_phone}</dd>
        </div>
      </dl>
      <p className="mt-4 text-xs text-slate-600">
        {emailMock
          ? "Email: demo mode — no real message was delivered. Add RESEND_API_KEY and a verified sender in backend/.env to send mail."
          : emailSent
            ? "Email: confirmation sent to your address."
            : "Email: pending or could not send."}
      </p>
      <div className="mt-4 rounded-xl border border-white/60 bg-white/70 p-3">
        <p className="text-sm font-medium text-ink">SMS confirmation (optional)</p>
        <p className="text-xs text-slate-500">We only text you if you opt in. The message includes provider, date/time, and office phone.</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={smsOptIn === true}
            onClick={() => onSmsChoice(true)}
            className="rounded-lg bg-kyron-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-kyron-700 disabled:opacity-50"
          >
            Yes, send SMS
          </button>
          <button
            type="button"
            disabled={smsOptIn === false}
            onClick={() => onSmsChoice(false)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            No thanks
          </button>
        </div>
        {smsOptIn === false ? (
          <p className="mt-2 text-xs text-slate-600">SMS: You declined text reminders.</p>
        ) : null}
        {smsOptIn === true ? (
          <div className="mt-2 space-y-1 text-xs">
            {smsSent && !smsMock ? (
              <p className="text-slate-600">✓ SMS confirmation sent to your phone.</p>
            ) : null}
            {!smsSent ? (
              <p className="text-slate-600">SMS confirmation could not be sent. Please check your phone number.</p>
            ) : null}
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}
