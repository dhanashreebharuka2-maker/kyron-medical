"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="font-display text-xl font-semibold text-ink">Something went wrong</p>
      <p className="max-w-md text-sm text-slate-600">{error.message || "An unexpected error occurred."}</p>
      <button
        type="button"
        onClick={() => reset()}
        className="rounded-xl bg-kyron-600 px-5 py-2.5 text-sm font-medium text-white shadow-glass hover:bg-kyron-700"
      >
        Try again
      </button>
    </div>
  );
}
