"use client";

type Chip = { label: string; message: string };

type Props = {
  chips: Chip[];
  onSelect: (message: string) => void;
};

export function QuickActions({ chips, onSelect }: Props) {
  if (!chips.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {chips.map((c) => (
        <button
          key={c.label}
          type="button"
          onClick={() => onSelect(c.message)}
          className="rounded-full border border-slate-200/80 bg-white/70 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm backdrop-blur transition hover:border-kyron-300 hover:bg-white hover:text-kyron-900"
        >
          {c.label}
        </button>
      ))}
    </div>
  );
}
