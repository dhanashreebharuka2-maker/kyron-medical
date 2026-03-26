"use client";

import { motion } from "framer-motion";
import { FormEvent, useMemo, useState } from "react";

const STEPS = [
  { key: "first_name", label: "First name", input: "text" as const, placeholder: "Jane", autoComplete: "given-name" },
  { key: "last_name", label: "Last name", input: "text" as const, placeholder: "Doe", autoComplete: "family-name" },
  { key: "dob", label: "Date of birth", input: "date" as const, placeholder: "", autoComplete: "bday" },
  { key: "phone", label: "Phone number", input: "tel" as const, placeholder: "(512) 555-0100", autoComplete: "tel" },
  { key: "email", label: "Email", input: "email" as const, placeholder: "you@example.com", autoComplete: "email" },
  {
    key: "reason_for_visit",
    label: "Reason for visit",
    input: "textarea" as const,
    placeholder: "e.g. follow-up for knee pain",
    autoComplete: "off",
  },
] as const;

type IntakeKey = (typeof STEPS)[number]["key"];

export type IntakePayload = {
  first_name: string;
  last_name: string;
  dob: string;
  phone: string;
  email: string;
  reason_for_visit: string;
};

type Props = {
  onSubmit: (data: IntakePayload) => Promise<void>;
  onComplete: () => void;
};

export function InlineIntakeCard({ onSubmit, onComplete }: Props) {
  const [step, setStep] = useState(0);
  const [values, setValues] = useState<Partial<Record<IntakeKey, string>>>({});
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const current = STEPS[step];
  const total = STEPS.length;
  const progress = step + 1;

  const fieldValue = values[current.key] ?? "";

  function setField(v: string) {
    setValues((prev) => ({ ...prev, [current.key]: v }));
  }

  function validate(trimmed: string): boolean {
    if (!trimmed) {
      setErr("Please enter a value to continue.");
      return false;
    }
    if (current.key === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      setErr("Enter a valid email address.");
      return false;
    }
    setErr(null);
    return true;
  }

  async function onContinue(e: FormEvent) {
    e.preventDefault();
    const trimmed = fieldValue.trim();
    if (!validate(trimmed)) return;

    const merged = { ...values, [current.key]: trimmed } as Record<IntakeKey, string>;

    if (step < total - 1) {
      setValues(merged);
      setStep((s) => s + 1);
      return;
    }

    const payload: IntakePayload = {
      first_name: merged.first_name,
      last_name: merged.last_name,
      dob: merged.dob,
      phone: merged.phone,
      email: merged.email,
      reason_for_visit: merged.reason_for_visit,
    };

    setLoading(true);
    setErr(null);
    try {
      await onSubmit(payload);
      onComplete();
    } catch {
      setErr("Could not save. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  function goBack() {
    if (step <= 0) return;
    setStep((s) => s - 1);
    setErr(null);
  }

  const barPct = useMemo(() => (progress / total) * 100, [progress, total]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-kyron-200/70 bg-gradient-to-b from-white to-sky-50/40 p-4 shadow-inner backdrop-blur-xl"
    >
      <p className="text-[11px] font-semibold uppercase tracking-wide text-kyron-700">Patient intake</p>
      <p className="mt-1 text-sm text-slate-600">
        We&apos;ll collect a few details here in the chat — one question at a time. Not medical advice.
      </p>
      <div className="mt-3 flex items-center gap-2">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200/80">
          <div
            className="h-full rounded-full bg-gradient-to-r from-kyron-500 to-kyron-600 transition-[width]"
            style={{ width: `${barPct}%` }}
          />
        </div>
        <span className="text-[11px] font-medium tabular-nums text-slate-500">
          {progress}/{total}
        </span>
      </div>
      <form onSubmit={onContinue} className="mt-4 space-y-3">
        <label className="block text-xs font-medium text-slate-600">
          {current.label}
          {current.input === "textarea" ? (
            <textarea
              value={fieldValue}
              onChange={(e) => setField(e.target.value)}
              rows={3}
              placeholder={current.placeholder}
              autoComplete={current.autoComplete}
              className="mt-1.5 w-full resize-none rounded-xl border border-slate-200/90 bg-white px-3 py-2.5 text-sm text-ink shadow-inner outline-none ring-kyron-400 focus:ring-2"
            />
          ) : (
            <input
              type={current.input === "date" ? "date" : current.input}
              value={fieldValue}
              onChange={(e) => setField(e.target.value)}
              placeholder={current.placeholder}
              autoComplete={current.autoComplete}
              className="mt-1.5 w-full rounded-xl border border-slate-200/90 bg-white px-3 py-2.5 text-sm text-ink shadow-inner outline-none ring-kyron-400 focus:ring-2"
            />
          )}
        </label>
        {err && <p className="text-sm text-red-600">{err}</p>}
        <div className="flex flex-wrap justify-end gap-2 pt-1">
          {step > 0 && (
            <button
              type="button"
              onClick={goBack}
              disabled={loading}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Back
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-kyron-600 px-5 py-2 text-sm font-semibold text-white shadow-md shadow-kyron-600/20 hover:bg-kyron-700 disabled:opacity-60"
          >
            {loading ? "Saving…" : step < total - 1 ? "Continue" : "Save & continue"}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
