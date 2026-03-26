"use client";

import { useState } from "react";
import { voiceHandoff } from "@/lib/api";
import type { VoiceHandoffApiResponse } from "@/lib/api";

type Props = {
  sessionId: string;
  patientPhone?: string;
  onHandoff?: (result: VoiceHandoffApiResponse) => void;
};

export function VoiceHandoffBar({ sessionId, patientPhone, onHandoff }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VoiceHandoffApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const maskedPhone = patientPhone
    ? `(***) ***-${patientPhone.replace(/\D/g, "").slice(-4)}`
    : null;

  async function handleCall() {
    setLoading(true);
    setError(null);
    try {
      const res = await voiceHandoff(sessionId);
      setResult(res);
      onHandoff?.(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Call failed");
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <div className="flex items-center gap-2 border-t border-slate-200/60 bg-emerald-50/80 px-4 py-3 sm:px-6">
        <svg className="h-4 w-4 shrink-0 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm font-medium text-emerald-700">Calling you now</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 border-t border-slate-200/60 bg-white/60 px-4 py-3 sm:px-6">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-slate-700">Continue by phone</p>
        {maskedPhone && (
          <p className="text-xs text-slate-500">We&apos;ll call {maskedPhone}</p>
        )}
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <button
        onClick={() => void handleCall()}
        disabled={loading || !patientPhone}
        className="flex shrink-0 items-center gap-1.5 rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
        </svg>
        {loading ? "Calling…" : "Call me"}
      </button>
    </div>
  );
}
