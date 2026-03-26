"use client";

import { motion } from "framer-motion";
import { FormEvent, useState } from "react";

type Props = {
  sessionId: string;
  embedded?: boolean;
  onSubmitRefill: (data: {
    medication: string;
    notes: string;
    pharmacy: string;
    urgency: string;
  }) => Promise<void>;
};

const URGENCY = [
  { value: "routine", label: "Routine (standard review)" },
  { value: "soon", label: "Soon — within a few days" },
  { value: "urgent", label: "Urgent — same day if possible" },
] as const;

export function RefillRequestCard({ sessionId, embedded, onSubmitRefill }: Props) {
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [draft, setDraft] = useState({ medication: "", notes: "", pharmacy: "", urgency: "routine" });

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    if (step === 1) {
      if (!draft.medication.trim()) {
        setErr("Please enter the medication name.");
        return;
      }
      setStep(2);
      return;
    }
    setLoading(true);
    try {
      await onSubmitRefill({
        medication: draft.medication.trim(),
        notes: draft.notes.trim(),
        pharmacy: draft.pharmacy.trim(),
        urgency: draft.urgency,
      });
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
          ? "rounded-2xl border border-violet-200/70 bg-gradient-to-b from-violet-50/90 to-white/85 p-4 shadow-inner backdrop-blur-xl"
          : "rounded-2xl border border-white/50 bg-white/55 p-5 shadow-glass backdrop-blur-2xl"
      }
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-display text-base font-semibold text-ink sm:text-lg">Prescription refill</h3>
        <span className="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-800">
          Step {step} of 2
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        We route this to the practice. No dosing advice or approvals here — a clinician reviews requests.
      </p>
      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        {step === 1 ? (
          <>
            <label className="block text-xs font-medium text-slate-500">
              Medication name
              <input
                value={draft.medication}
                onChange={(e) => setDraft((d) => ({ ...d, medication: e.target.value }))}
                placeholder="e.g. Lisinopril 10mg tablet"
                className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-violet-400 focus:ring-2"
                autoComplete="off"
              />
            </label>
            <label className="block text-xs font-medium text-slate-500">
              Notes for the team (optional)
              <textarea
                value={draft.notes}
                onChange={(e) => setDraft((d) => ({ ...d, notes: e.target.value }))}
                rows={2}
                placeholder="Strength changes, prescriber, last fill date…"
                className="mt-1 w-full resize-none rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-violet-400 focus:ring-2"
              />
            </label>
          </>
        ) : (
          <>
            <p className="text-xs text-slate-600">
              Medication: <span className="font-medium text-ink">{draft.medication}</span>
            </p>
            <label className="block text-xs font-medium text-slate-500">
              Pharmacy (optional)
              <input
                value={draft.pharmacy}
                onChange={(e) => setDraft((d) => ({ ...d, pharmacy: e.target.value }))}
                placeholder="Name and city, or chain + store #"
                className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-violet-400 focus:ring-2"
                autoComplete="off"
              />
            </label>
            <label className="block text-xs font-medium text-slate-500">
              How soon do you need it?
              <select
                value={draft.urgency}
                onChange={(e) => setDraft((d) => ({ ...d, urgency: e.target.value }))}
                className="mt-1 w-full rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-ink outline-none ring-violet-400 focus:ring-2"
              >
                {URGENCY.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
        {err && <p className="text-sm text-red-600">{err}</p>}
        <div className="flex flex-wrap justify-end gap-2">
          {step === 2 ? (
            <button
              type="button"
              onClick={() => setStep(1)}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Back
            </button>
          ) : null}
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-medium text-white shadow-glass transition hover:bg-violet-700 disabled:opacity-60"
          >
            {loading ? "Submitting…" : step === 1 ? "Continue" : "Submit refill request"}
          </button>
        </div>
      </form>
      {!embedded && (
        <p className="mt-2 text-[10px] text-slate-400">Session: {sessionId.slice(0, 8)}…</p>
      )}
    </motion.div>
  );
}
