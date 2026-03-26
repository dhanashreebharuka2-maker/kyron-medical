import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-4 text-center">
      <p className="font-display text-2xl font-semibold text-ink">Page not found</p>
      <p className="max-w-lg text-sm text-slate-600">
        This URL isn’t part of the Kyron patient assistant. The app home is at{" "}
        <code className="rounded bg-slate-200 px-1.5 py-0.5 text-xs">/</code> on the same host where you run{" "}
        <code className="rounded bg-slate-200 px-1.5 py-0.5 text-xs">npm run dev</code> in{" "}
        <code className="rounded bg-slate-200 px-1.5 py-0.5 text-xs">frontend/</code>.
      </p>
      <p className="max-w-lg text-sm text-slate-600">
        <strong className="text-slate-800">Important:</strong> Next.js often uses a port <em>other than</em> 3000 if that
        port is busy. In the terminal where the dev server started, use the line that says{" "}
        <code className="rounded bg-slate-200 px-1.5 py-0.5 text-xs">Local: http://localhost:…</code> — that is the
        correct URL (for example <code className="rounded bg-slate-200 px-1.5 py-0.5 text-xs">3007</code>).
      </p>
      <p className="max-w-lg text-xs text-slate-500">
        The API runs separately on port 8000 — that is not the web UI. If the home page looks wrong, stop dev, run{" "}
        <code className="rounded bg-slate-100 px-1 py-0.5">rm -rf .next</code>, then <code className="rounded bg-slate-100 px-1 py-0.5">npm run dev</code> again.
      </p>
      <Link
        href="/"
        className="rounded-xl bg-kyron-600 px-5 py-2.5 text-sm font-medium text-white shadow-glass hover:bg-kyron-700"
      >
        Try home (/)
      </Link>
    </div>
  );
}
