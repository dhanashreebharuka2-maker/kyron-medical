#!/usr/bin/env bash
# Quick Cloudflare tunnel for local dev (requires: brew install cloudflare/cloudflare/cloudflared).
# Default: forward public HTTPS → Next.js (port 3000) so /api/* rewrites to FastAPI — use this for Bland webhooks.
# Alternative: ./scripts/tunnel.sh api → FastAPI :8000 directly (no Next rewrites; same /api routes on FastAPI).
set -euo pipefail

TARGET="${1:-next}"
case "$TARGET" in
  next)
    URL="http://127.0.0.1:3000"
    echo "Tunnel → Next.js at $URL (ensure npm run dev is running; API rewrites to FastAPI)."
    ;;
  api)
    URL="http://127.0.0.1:8000"
    echo "Tunnel → FastAPI at $URL (ensure uvicorn is running on :8000)."
    ;;
  *)
    echo "Usage: $0 [next|api]" >&2
    echo "  next  — default; use with BLAND_WEBHOOK_URL=https://<host>/api/voice/bland-webhook" >&2
    echo "  api   — expose backend only; same webhook path on :8000" >&2
    exit 1
    ;;
esac

exec cloudflared tunnel --url "$URL"
