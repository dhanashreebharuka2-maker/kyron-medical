"use client";

import { motion } from "framer-motion";

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 rounded-2xl border border-white/40 bg-white/60 px-4 py-3 backdrop-blur-xl">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-2 w-2 rounded-full bg-kyron-400"
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
      <span className="ml-2 text-xs text-slate-500">Kyron is typing…</span>
    </div>
  );
}
