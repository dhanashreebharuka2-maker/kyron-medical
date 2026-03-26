"use client";

import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle: string;
  eyebrow?: string;
  children: ReactNode;
  banner?: ReactNode;
};

export function AppShell({ title, subtitle, eyebrow = "Kyron Medical", children, banner }: Props) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-white/30 bg-white/35 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-kyron-700">{eyebrow}</p>
          <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">{title}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">{subtitle}</p>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {banner}
        {children}
      </main>
    </div>
  );
}
