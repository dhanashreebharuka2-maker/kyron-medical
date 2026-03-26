"use client";

import { motion } from "framer-motion";
import type { ChangeEvent, KeyboardEvent } from "react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
};

export function ChatComposer({ value, onChange, onSend, disabled }: Props) {
  return (
    <div className="shrink-0 border-t border-slate-200/70 bg-gradient-to-b from-white/95 to-sky-50/30 p-4 sm:p-5">
      <label htmlFor="kyron-chat-input" className="flex items-center gap-2 text-sm font-semibold text-ink">
        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-kyron-600 text-white shadow-md shadow-kyron-600/20">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="opacity-95" aria-hidden>
            <path
              d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        Message
      </label>
      <p id="kyron-chat-hint" className="mt-1 text-xs text-slate-500">
        Press Enter to send — your conversation stays in this panel.
      </p>
      <div className="mt-3 flex gap-2">
        <input
          id="kyron-chat-input"
          type="text"
          value={value}
          onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
          onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder="Ask anything or describe what you need…"
          disabled={disabled}
          autoComplete="off"
          aria-describedby="kyron-chat-hint"
          className="flex-1 rounded-2xl border border-slate-200/90 bg-white px-4 py-3.5 text-sm text-ink shadow-inner outline-none ring-0 transition focus:border-kyron-400 focus:shadow-[0_0_0_3px_rgba(14,165,233,0.15)] disabled:opacity-50"
        />
        <motion.button
          whileTap={{ scale: 0.98 }}
          type="button"
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="shrink-0 rounded-2xl bg-gradient-to-b from-kyron-600 to-kyron-700 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-kyron-600/25 transition hover:from-kyron-500 hover:to-kyron-600 disabled:opacity-45"
        >
          Send
        </motion.button>
      </div>
    </div>
  );
}
