"use client";

import { motion } from "framer-motion";
import { FormEvent, useState } from "react";

type Props = {
  sessionId: string;
  /** When true, styled to sit inside the chat thread */
  embedded?: boolean;
  onSubmitted: () => void;
  onSubmitIntake: (data: {
    first_name: string;
    last_name: string;
    dob: string;
    phone: string;
    email: string;
    reason_for_visit: string;
  }) => Promise<void>;
};

export function IntakeFormCard({ sessionId, embedded, onSubmitted, onSubmitIntake }: Props) {
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    const fd = new FormData(e.currentTarget);
    const first_name = String(fd.get("first_name") || "").trim();
    const last_name = String(fd.get("last_name") || "").trim();
    const dob = String(fd.get("dob") || "").trim();
    const phone = String(fd.get("phone") || "").trim();
    const email = String(fd.get("email") || "").trim();
    const reason_for_visit = String(fd.get("reason_for_visit") || "").trim();
    if (!first_name || !last_name || !dob || !phone || !email || !reason_for_visit) {
      setErr("Please fill in all fields.");
      return;
    }
    setLoading(true);
    try {
      await onSubmitIntake({ first_name, last_name, dob, phone, email, reason_for_visit });
      onSubmitted();
    } catch {
      setErr("Could not save. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={
        embedded
          ? "rounded-2xl border border-kyron-200/60 bg-white/85 p-4 shadow-inner backdrop-blur-xl"
          : "rounded-2xl border border-white/50 bg-white/55 p-5 shadow-glass backdrop-blur-2xl"
      }
    >
      <h3 className="font-display text-base font-semibold text-ink sm:text-lg">Patient intake</h3>
      <p className="mt-1 text-sm text-slate-600">
        We need a few details to schedule. This assistant does not provide medical advice.
      </p>
      <form onSubmit={onSubmit} className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-xs font-medium text-slate-500">
          First name
          <input
            name="first_name"
            className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-kyron-400 focus:ring-2"
            autoComplete="given-name"
          />
        </label>
        <label className="text-xs font-medium text-slate-500">
          Last name
          <input
            name="last_name"
            className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-kyron-400 focus:ring-2"
            autoComplete="family-name"
          />
        </label>
        <label className="text-xs font-medium text-slate-500">
          Date of birth
          <input
            name="dob"
            type="date"
            className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-kyron-400 focus:ring-2"
          />
        </label>
        <label className="text-xs font-medium text-slate-500">
          Phone
          <input
            name="phone"
            placeholder="5125550100"
            className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-kyron-400 focus:ring-2"
            autoComplete="tel"
          />
        </label>
        <label className="sm:col-span-2 text-xs font-medium text-slate-500">
          Email
          <input
            name="email"
            type="email"
            className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-kyron-400 focus:ring-2"
            autoComplete="email"
          />
        </label>
        <label className="sm:col-span-2 text-xs font-medium text-slate-500">
          Reason for visit
          <textarea
            name="reason_for_visit"
            rows={2}
            placeholder="e.g. knee pain after running, or a rash on my arm"
            className="mt-1 w-full resize-none rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-kyron-400 focus:ring-2"
          />
        </label>
        {err && <p className="sm:col-span-2 text-sm text-red-600">{err}</p>}
        <div className="sm:col-span-2 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-kyron-600 px-5 py-2.5 text-sm font-medium text-white shadow-glass transition hover:bg-kyron-700 disabled:opacity-60"
          >
            {loading ? "Saving…" : "Save & continue"}
          </button>
        </div>
      </form>
      {!embedded && (
        <p className="mt-2 text-[10px] text-slate-400">Session: {sessionId.slice(0, 8)}…</p>
      )}
    </motion.div>
  );
}
