"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { BookingConfirmationCard } from "@/components/BookingConfirmationCard";
import { ChatPanel, type ChatLine } from "@/components/ChatPanel";
import { InlineIntakeCard } from "@/components/InlineIntakeCard";
import { OfficeInfoSidebar } from "@/components/OfficeInfoSidebar";
import { ProviderMatchCard } from "@/components/ProviderMatchCard";
import { RefillRequestCard } from "@/components/RefillRequestCard";
import { SlotPickerCard } from "@/components/SlotPickerCard";
import {
  bookSlot,
  createSession,
  sendChat,
  smsOptIn as smsOptInApi,
  slotQuery,
  submitIntake,
  submitRefill,
} from "@/lib/api";
import type { SessionState } from "@/types/session";

const CHIPS = [
  { label: "Book appointment", message: "I would like to schedule an appointment." },
  { label: "Prescription refill", message: "I need help with a prescription refill request." },
  { label: "Office & hours", message: "What is your office address and hours?" },
];

function isAbortError(e: unknown): boolean {
  if (e instanceof DOMException && e.name === "AbortError") return true;
  if (e instanceof Error && e.name === "AbortError") return true;
  return false;
}

export default function HomePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<SessionState | null>(null);
  const [sessionLoadError, setSessionLoadError] = useState(false);
  const [messages, setMessages] = useState<ChatLine[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [busy, setBusy] = useState(false);
  const [bookBusy, setBookBusy] = useState(false);

  const uiHints = useMemo(() => {
    if (!session) return null;
    const s = session;
    return {
      show_intake: s.workflow === "scheduling" && !s.intake_complete,
      show_refill: s.workflow === "refill" && !s.refill_complete,
      show_provider: Boolean(s.matched_provider) || Boolean(s.match_error),
      show_slots: Boolean(
        s.intake_complete && s.matched_provider_id && !s.booking_confirmed && !s.match_error
      ),
    };
  }, [session]);

  const office = session?.office as
    | {
        name: string;
        address_line1: string;
        address_line2?: string;
        city: string;
        state: string;
        zip: string;
        phone: string;
        hours: Record<string, string>;
        parking?: string;
      }
    | undefined;

  const chatEmbedSignature = useMemo(
    () =>
      [
        sessionId ?? "",
        uiHints?.show_intake ? "i" : "",
        uiHints?.show_refill ? "r" : "",
        uiHints?.show_provider ? "p" : "",
        uiHints?.show_slots ? "s" : "",
        session?.booking_confirmed ? "b" : "",
      ].join("|"),
    [sessionId, uiHints, session?.booking_confirmed]
  );

  const chatEmbeddedContent = useMemo(() => {
    if (!sessionId || !session || !uiHints) return null;
    const hasPanels =
      uiHints.show_refill ||
      uiHints.show_intake ||
      uiHints.show_provider ||
      uiHints.show_slots ||
      (session.booking_confirmed && session.booking);
    if (!hasPanels) return null;
    return (
      <>
        {uiHints.show_refill && (
          <RefillRequestCard
            embedded
            sessionId={sessionId}
            onSubmitRefill={async (data) => {
              const r = await submitRefill(sessionId, {
                medication: data.medication,
                notes: data.notes,
                pharmacy: data.pharmacy,
                urgency: data.urgency,
              });
              const sess = r.session as SessionState;
              setSession(sess);
              const last = sess.messages?.at(-1);
              if (last?.role === "assistant") {
                setMessages((m) => [...m, { role: "assistant", content: last.content }]);
              }
            }}
          />
        )}
        {uiHints.show_intake && (
          <InlineIntakeCard
            onSubmit={async (data) => {
              const r = await submitIntake(sessionId, data);
              setSession(r.session as SessionState);
            }}
            onComplete={() =>
              setMessages((m) => [
                ...m,
                {
                  role: "assistant",
                  content:
                    "Your details are saved. Review the suggested provider and pick a time below when they appear.",
                },
              ])
            }
          />
        )}
        {session && uiHints.show_provider && (
          <ProviderMatchCard embedded provider={session.matched_provider} errorText={session.match_error} />
        )}
        {session && uiHints.show_slots && (
          <SlotPickerCard
            slots={session.shown_slots ?? []}
            selectedId={session.selected_slot_id ?? null}
            disabled={bookBusy}
            onFilter={async (q) => {
              const r = await slotQuery(sessionId, q);
              setSession(r.session as SessionState);
            }}
            onSelect={async (slotId) => {
              setBookBusy(true);
              try {
                const r = await bookSlot(sessionId, slotId);
                if (r.success) {
                  setSession(r.session as SessionState);
                  setMessages((m) => [...m, { role: "assistant", content: r.message }]);
                } else {
                  setMessages((m) => [...m, { role: "assistant", content: r.message }]);
                }
              } catch {
                setMessages((m) => [...m, { role: "assistant", content: "Booking failed. Try another slot." }]);
              } finally {
                setBookBusy(false);
              }
            }}
          />
        )}
        {session?.booking_confirmed && session.booking && (
          <BookingConfirmationCard
            embedded
            booking={session.booking}
            emailSent={session.email_sent}
            emailMock={session.email_mock}
            smsOptIn={session.sms_opt_in}
            smsSent={session.sms_sent}
            smsMock={session.sms_mock}
            smsLastError={session.sms_last_error}
            smsMessageSid={session.sms_message_sid}
            onSmsChoice={async (optIn) => {
              try {
                const r = await smsOptInApi(sessionId, optIn);
                setSession(r.session);
              } catch {
                /* noop */
              }
            }}
          />
        )}
      </>
    );
  }, [sessionId, uiHints, session, bookBusy]);

  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      setSessionLoadError(false);
      try {
        const { session_id, session: s } = await createSession(ac.signal);
        setSessionId(session_id);
        setSession(s as SessionState);
        setSessionLoadError(false);
        setMessages([
          {
            role: "assistant",
            content:
              "Hi, I'm Alex, an AI assistant for Kyron Medical. How can I help you today? I can help you schedule an appointment, route a refill request to our team, or share our office details. I don’t provide medical advice — for clinical questions, please contact your care team.",
          },
        ]);
      } catch (e) {
        if (isAbortError(e)) return;
        setSessionId(null);
        setSession(null);
        setSessionLoadError(true);
        setMessages([
          {
            role: "assistant",
            content:
              "Could not reach the server. Start the API from the backend folder (uvicorn), then click Retry below or refresh the page.",
          },
        ]);
      }
    })();
    return () => ac.abort();
  }, []);

  const pushChat = useCallback(async (text: string) => {
    if (!sessionId || !text.trim()) return;
    const userLine: ChatLine = { role: "user", content: text.trim() };
    setMessages((m) => [...m, userLine]);
    setTyping(true);
    setBusy(true);
    try {
      const res = await sendChat(sessionId, text.trim());
      setSession(res.session as SessionState);
      setMessages((m) => [...m, { role: "assistant", content: res.assistant_message }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally {
      setTyping(false);
      setBusy(false);
    }
  }, [sessionId]);

  const onSend = () => {
    const t = input;
    setInput("");
    void pushChat(t);
  };

  const retrySession = useCallback(() => {
    setBusy(true);
    setSessionLoadError(false);
    void (async () => {
      try {
        const { session_id, session: s } = await createSession();
        setSessionId(session_id);
        setSession(s as SessionState);
        setSessionLoadError(false);
        setMessages([
          {
            role: "assistant",
            content:
              "Hi, I'm Alex, an AI assistant for Kyron Medical. How can I help you today? I can help you schedule an appointment, route a refill request to our team, or share our office details. I don’t provide medical advice — for clinical questions, please contact your care team.",
          },
        ]);
      } catch {
        setSessionId(null);
        setSession(null);
        setSessionLoadError(true);
        setMessages([
          {
            role: "assistant",
            content:
              "Still could not reach the server. Confirm the API is running on port 8000 and try again.",
          },
        ]);
      } finally {
        setBusy(false);
      }
    })();
  }, []);

  return (
    <AppShell
      title="Patient assistant"
      subtitle="Schedule visits, route refill requests, and get office information — all in one secure conversation. Voice handoff preserves your session context."
      banner={
        sessionLoadError ? (
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-200/90 bg-amber-50/95 px-4 py-3 text-sm text-amber-950 shadow-inner backdrop-blur">
            <p>
              <span className="font-semibold">Backend not reachable.</span> From{" "}
              <code className="rounded bg-amber-100/80 px-1.5 py-0.5 text-xs">backend/</code> run:{" "}
              <code className="rounded bg-amber-100/80 px-1.5 py-0.5 text-xs">
                uvicorn main:app --reload --host 127.0.0.1 --port 8000
              </code>
            </p>
            <button
              type="button"
              onClick={retrySession}
              disabled={busy}
              className="rounded-xl bg-amber-800 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-900 disabled:opacity-50"
            >
              Retry connection
            </button>
          </div>
        ) : null
      }
    >
      <div className="grid gap-4 sm:gap-6 lg:grid-cols-12 lg:items-start lg:gap-8">
        <div className="min-w-0 lg:col-span-8">
          <ChatPanel
            messages={messages}
            typing={typing}
            embeddedContent={chatEmbeddedContent}
            embedSignature={chatEmbedSignature}
            input={input}
            onInputChange={setInput}
            onSend={onSend}
            disabled={busy || !sessionId}
            chips={CHIPS}
            onChip={(msg) => void pushChat(msg)}
            connecting={!sessionId && !sessionLoadError}
          />
        </div>
        <div className="min-w-0 lg:col-span-4">
          <OfficeInfoSidebar
            office={office}
            session={session}
            sessionId={sessionId}
            onSessionUpdate={(s) => setSession(s)}
          />
        </div>
      </div>
    </AppShell>
  );
}
