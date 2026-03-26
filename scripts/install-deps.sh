#!/usr/bin/env bash
# Install backend (Python) and frontend (Node) dependencies for Kyron Medical.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Backend (Python venv + pip)"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r requirements.txt

echo ""
echo "==> Frontend (npm)"
cd "$ROOT/frontend"
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Install Node.js 18+ (https://nodejs.org) or use nvm, then run:"
  echo "  cd frontend && npm install"
  exit 0
fi
npm install

echo ""
echo "Done. Backend: source backend/.venv/bin/activate && uvicorn main:app --reload"
echo "       Frontend: cd frontend && npm run dev"
