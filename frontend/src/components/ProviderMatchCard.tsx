"use client";

import { motion } from "framer-motion";
import type { Provider } from "@/types/session";

type Props = {
  provider?: Provider | null;
  errorText?: string | null;
  embedded?: boolean;
};

function providerCardClass(embedded: boolean | undefined) {
  return embedded
    ? "rounded-2xl border border-kyron-200/60 bg-gradient-to-br from-white/90 to-kyron-50/80 p-4 shadow-inner backdrop-blur-xl"
    : "rounded-2xl border border-white/50 bg-gradient-to-br from-white/80 to-kyron-50/90 p-5 shadow-glass backdrop-blur-2xl";
}

export function ProviderMatchCard({ provider, errorText, embedded }: Props) {
  if (errorText && !provider) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className={
          embedded
            ? "rounded-2xl border border-amber-200/80 bg-amber-50/90 p-4 text-sm text-amber-900 backdrop-blur-xl"
            : "rounded-2xl border border-amber-200/80 bg-amber-50/80 p-4 text-sm text-amber-900 backdrop-blur-xl"
        }
      >
        {errorText}
      </motion.div>
    );
  }

  if (!provider) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={providerCardClass(embedded)}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-kyron-600">Suggested provider</p>
      <h3
        className={`mt-1 font-display font-semibold text-ink ${embedded ? "text-lg sm:text-xl" : "text-xl"}`}
      >
        {provider.full_name}
      </h3>
      <p className="text-sm text-kyron-700">{provider.specialty}</p>
      <p className="mt-2 text-sm text-slate-600">{provider.body_part_focus}</p>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{provider.description}</p>
    </motion.div>
  );
}
