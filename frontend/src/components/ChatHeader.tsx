"use client";

type Props = {
  title?: string;
  subtitle?: string;
  status?: string;
};

export function ChatHeader({
  title = "Alex · Kyron Medical",
  subtitle = "Administrative help only — not medical advice",
  status = "Online",
}: Props) {
  return (
    <div className="flex items-start gap-3 border-b border-slate-200/60 bg-gradient-to-r from-white/90 to-sky-50/50 px-5 py-4 backdrop-blur-xl sm:px-6">
      <div
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-kyron-500 to-kyron-700 text-sm font-bold text-white shadow-lg shadow-kyron-500/25"
        aria-hidden
      >
        K
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="font-display text-lg font-semibold tracking-tight text-ink sm:text-xl">{title}</h2>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200/80 bg-emerald-50/90 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-800">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
            </span>
            {status}
          </span>
        </div>
        <p className="mt-0.5 text-xs leading-relaxed text-slate-600 sm:text-sm">{subtitle}</p>
      </div>
    </div>
  );
}
