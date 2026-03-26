# Kyron Medical — Patient AI Scheduling MVP

Local-first monorepo: a **Next.js** patient chat UI talks to a **FastAPI** backend for session state, provider matching, mock scheduling, notifications (mocked or live), and voice handoff payloads.

## Architecture (interview-friendly)

| Layer | Responsibility |
|--------|----------------|
| **Next.js (`/frontend`)** | Chat UI, glassmorphism styling, Framer Motion, intake form, slot picker, confirmation & voice handoff buttons. Calls `/api/*` (proxied to FastAPI in dev). |
| **FastAPI (`/backend`)** | Sessions (in-memory), chat orchestration (OpenAI JSON mode when `OPENAI_API_KEY` is set; deterministic mock otherwise), keyword provider matching, slot filtering, booking, Resend/Twilio hooks with graceful mocks. |

Session state is a plain dict you can swap later for **Redis** or a database without changing the UI contract.

## Prerequisites

- **Python** 3.9+ (tested with 3.9)
- **Node.js** 18+ and **npm** (for the frontend)

## Local development

One-shot install (Python venv + pip, then `npm install` if Node is available):

```bash
./scripts/install-deps.sh
```

### 1. Backend

Use **Python 3.11+** linked against **OpenSSL 3** (not Apple’s default `/usr/bin/python3`, which ships with old LibreSSL and can fail modern HTTPS APIs with `TLSV1_ALERT_PROTOCOL_VERSION`). On macOS, install e.g. `brew install python@3.12` and create the venv with `$(brew --prefix python@3.12)/bin/python3 -m venv .venv`.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional: add OPENAI_API_KEY, RESEND_API_KEY, Twilio vars
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: `http://127.0.0.1:8000/docs`
- Health: `GET /health`

Tip: if you see frequent reloads during dev after installing packages, start Uvicorn with
`--reload-exclude .venv/*` (or run without `--reload`) to avoid watching the virtualenv.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The Next.js dev server **rewrites** `/api/*` and `/health` to the backend URL from `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`), so the browser stays same-origin and you avoid CORS issues during development.

Copy `frontend/.env.example` to `frontend/.env.local` if you need a non-default API URL.

### Cloudflare tunnel (Vapi webhooks)

Post-call events need a **public HTTPS** URL that reaches your backend route **`/api/voice/vapi-webhook`**. In the **Vapi dashboard**, set that URL on your assistant (Server URL / webhook) — the app does **not** send `serverUrl` on `POST /call` (Vapi rejects it).

Use Cloudflare’s quick tunnel to expose local dev:

1. **Terminal A — backend:** `cd backend && source .venv/bin/activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000`
2. **Terminal B — frontend:** `cd frontend && npm run dev` (Next on `http://localhost:3000`)
3. **Terminal C — tunnel:** either `cd frontend && npm run tunnel` or from the repo root: `./scripts/tunnel.sh`

`cloudflared` prints a URL like `https://something.trycloudflare.com`. Paste **`https://something.trycloudflare.com/api/voice/vapi-webhook`** into Vapi’s assistant webhook field (and optionally keep the same string in `VAPI_WEBHOOK_URL` in `backend/.env` as a note for yourself).

Quick tunnels get a **new hostname each run**. For a stable URL, use a [named Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) instead.

**Direct API only:** `npm run tunnel:api` or `./scripts/tunnel.sh api` forwards to FastAPI `:8000` (no Next). Webhook path is still `/api/voice/vapi-webhook`.

**Vapi assistant prompt:** the backend sends the full voice instructions + session facts in **`assistantOverrides.variableValues.kyron_context`** (same content as before, without using `systemPrompt` on the API). In Vapi, set the assistant system prompt to **`{{kyron_context}}`** (or your short intro plus **`{{kyron_context}}`** on the next line) so each call receives the packaged context.

**SMS over the call (practical path — Textbelt via backend, not Vapi’s Twilio SMS widget):**

1. **Remove or disable** Vapi’s built-in **SMS** tool that asks for a Twilio “from” number — that path does not use `TEXTBELT_API_KEY` in this repo.
2. Add a **Custom / Server / HTTP** tool (name e.g. **`kyron_sms_opt_in`**) that your assistant can call with two arguments: **`session_id`** (string) and **`opt_in`** (boolean).
3. Point the tool at your **public** API (same Cloudflare tunnel as webhooks):
   - **POST** `https://YOUR-TUNNEL.trycloudflare.com/api/voice/sms-opt-in`
   - **Headers:** `Content-Type: application/json`
   - **Body:** `{ "session_id": "<uuid>", "opt_in": true }` or `false`  
   Map **`session_id`** from the assistant variable **`kyron_session_id`** (the backend also sends it in `assistantOverrides.variableValues` on each outbound call).
4. **`TEXTBELT_API_KEY`** (or Twilio) in `backend/.env` — the **FastAPI** app sends the actual SMS when the appointment is confirmed (voice webhook or web booking), not Vapi’s SMS UI.

The legacy route **`POST /api/notify/sms-opt-in`** is the same logic as **`/api/voice/sms-opt-in`** (chat checkbox and Vapi tool can use either).

**TypeScript / IDE errors (e.g. “Cannot find module `react`”, JSX has implicit `any`)**  
These almost always mean dependencies are not installed. From `frontend/`, run **`npm install`** once so `node_modules` exists and the editor can load `@types/react` and `framer-motion`. Reload the VS Code/Cursor window after installing if squiggles remain.

### 3. Try the happy path

1. Click **Book appointment** (or type naturally in chat).
2. Complete **Patient intake** (name, DOB, phone, email, reason for visit).
3. Review **matched provider** (keyword + semantic routing to one of four specialties).
4. **Pick a slot** (optional **Apply** filter for “Tuesday”, “morning”, “after 3”, etc.).
5. See **confirmation**; email/SMS are **simulated** unless credentials are set.
6. Use **Call me** to package chat context for voice; with **Vapi** (`VAPI_*` in `.env`), an outbound call is placed; otherwise demo mode returns the same structured context without dialing.

## Environment variables

| Location | Variable | Purpose |
|----------|----------|---------|
| `backend/.env` | `OPENAI_API_KEY` | Enables GPT-4o-mini JSON orchestration; omit to use built-in mock replies. |
| `backend/.env` | `RESEND_API_KEY` | Sends real email via [Resend](https://resend.com); omit → mock success. |
| `backend/.env` | `TWILIO_*` | SMS; omit → mock success for SMS. |
| `backend/.env` | `VAPI_API_KEY`, `VAPI_ASSISTANT_ID`, `VAPI_PHONE_NUMBER_ID` | Outbound voice via [Vapi](https://vapi.ai); omit → voice demo mode (no dial). Webhook URL is set on the assistant in Vapi (optional `VAPI_WEBHOOK_URL` in `.env` is documentation only). |
| `backend/.env` | `CORS_ORIGINS` | Comma-separated allowed origins in production (e.g. `https://app.example.com`). |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | Where Next.js rewrites `/api/*` in `next build` / production (default `http://127.0.0.1:8000`). |

See `backend/.env.example` and `frontend/.env.example`.

## Production build

**Frontend**

```bash
cd frontend
npm run build
npm start
```

Set `NEXT_PUBLIC_API_URL` to your public API origin before `npm run build` if the API is not colocated.

**Backend**

Run with Uvicorn/Gunicorn behind a process manager (systemd, PM2, etc.):

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

## AWS EC2 + HTTPS (outline)

This repo does **not** deploy automatically. A typical pattern:

1. **EC2** instance (Ubuntu): install Python venv, run Uvicorn on `127.0.0.1:8000` (or a UNIX socket).
2. **Nginx** (or Caddy) as reverse proxy: TLS termination (Let’s Encrypt), `proxy_pass` to Uvicorn, serve or proxy the Next.js app (either `next start` on another port or static export if you move to S3/CloudFront).
3. Set `CORS_ORIGINS` to your HTTPS frontend origin.
4. Set `NEXT_PUBLIC_API_URL` to the public API URL if the frontend is built as a separate host; alternatively serve both behind one domain with path-based routing.

## API surface (summary)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/session` | Create session |
| GET | `/api/session/{id}` | Read session |
| POST | `/api/chat` | Send message (`session_id` optional on first turn) |
| POST | `/api/session/{id}/intake` | Structured intake + reason → match + slots |
| POST | `/api/session/{id}/slot-query` | Natural-language slot filter |
| POST | `/api/book` | Confirm booking for `slot_id` |
| POST | `/api/notify/sms-opt-in` | SMS opt-in / send (mockable) |
| POST | `/api/voice/handoff` | Build voice context; optional Vapi outbound call |
| POST | `/api/voice/vapi-webhook` | Vapi post-call webhook (booking + email/SMS) |
| POST | `/api/notify/sms-opt-in` | SMS opt-in + send (chat / same as below) |
| POST | `/api/voice/sms-opt-in` | Same — **use this URL for the Vapi HTTP SMS opt-in tool** |
| GET | `/api/providers` | List hard-coded providers |

## Safety

System prompts and mock logic refuse **diagnosis, prescriptions, and clinical advice** and steer users to appropriate care; emergency phrases trigger a 911/ER message. **Not for real clinical use** — demo/MVP only.

## Assumptions

- US-style 10-digit phone numbers for SMS/voice helpers.
- In-memory sessions reset on server restart.
- Mock availability regenerates at import time (restart the server to refresh dates).
