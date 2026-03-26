"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import type { Slot } from "@/types/session";

type Props = {
  slots: Slot[];
  selectedId: string | null;
  onFilter: (q: string) => Promise<void>;
  onSelect: (slotId: string) => void;
  disabled?: boolean;
  embedded?: boolean;
};

function formatSlot(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
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

export function AppointmentSlotPicker({
  slots,
  selectedId,
  onFilter,
  onSelect,
  disabled,
  embedded,
}: Props) {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={
        embedded
          ? "rounded-2xl border border-kyron-200/60 bg-white/85 p-4 shadow-inner backdrop-blur-xl"
          : "rounded-2xl border border-white/50 bg-white/55 p-5 shadow-glass backdrop-blur-2xl"
      }
    >
      <h3 className="font-display text-base font-semibold text-ink sm:text-lg">Available times</h3>
      <p className="mt-1 text-sm text-slate-600">
        Type things like <span className="font-medium text-slate-700">Tuesday morning</span>,{" "}
        <span className="font-medium text-slate-700">tomorrow after 3</span>,{" "}
        <span className="font-medium text-slate-700">next week</span>, or{" "}
        <span className="font-medium text-slate-700">earliest</span> — in chat or here.
      </p>
      <div className="mt-3 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. Friday morning, tomorrow, earliest slot"
          className="flex-1 rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm outline-none ring-kyron-400 focus:ring-2"
        />
        <button
          type="button"
          disabled={loading || !q.trim()}
          onClick={async () => {
            setLoading(true);
            try {
              await onFilter(q.trim());
            } finally {
              setLoading(false);
            }
          }}
          className="rounded-xl bg-slate-800/90 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          {loading ? "…" : "Apply"}
        </button>
      </div>
      <div className="mt-4 grid max-h-64 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
        {slots.length === 0 && (
          <p className="col-span-full text-sm text-slate-500">No slots match. Try a different filter.</p>
        )}
        {slots.map((s) => (
          <button
            key={s.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(s.id)}
            className={`rounded-xl border px-3 py-3 text-left text-sm transition ${
              selectedId === s.id
                ? "border-kyron-500 bg-kyron-50 ring-2 ring-kyron-400"
                : "border-white/60 bg-white/70 hover:border-kyron-300"
            }`}
          >
            <span className="font-medium text-ink">{formatSlot(s.start_iso)}</span>
            <span className="mt-1 block text-xs text-slate-500">{s.duration_minutes} min</span>
          </button>
        ))}
      </div>
    </motion.div>
  );
}
