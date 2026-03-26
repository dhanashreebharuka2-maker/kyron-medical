"use client";

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { ChatComposer } from "./ChatComposer";
import { ChatHeader } from "./ChatHeader";
import type { ChatLine } from "./ChatMessages";
import { ChatMessages } from "./ChatMessages";
import { QuickActions } from "./QuickActions";

export type { ChatLine } from "./ChatMessages";

type Props = {
  messages: ChatLine[];
  typing?: boolean;
  embeddedContent?: ReactNode;
  embedSignature?: string;
  input: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
  chips?: { label: string; message: string }[];
  onChip?: (message: string) => void;
  /** True until first session / welcome message is ready */
  connecting?: boolean;
  /** Voice handoff strip above the composer */
  voiceBar?: ReactNode;
};

export function ChatPanel({
  messages,
  typing,
  embeddedContent,
  embedSignature,
  input,
  onInputChange,
  onSend,
  disabled,
  chips,
  onChip,
  connecting,
  voiceBar,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing, embedSignature]);

  return (
    <div className="flex h-full min-h-[min(78vh,920px)] flex-col overflow-hidden rounded-3xl border border-slate-200/60 bg-gradient-to-b from-white/95 via-white/90 to-sky-50/50 shadow-[0_8px_40px_-12px_rgba(15,23,42,0.18),0_24px_48px_-24px_rgba(14,165,233,0.12)] backdrop-blur-2xl">
      <ChatHeader />
      <div className="shrink-0 border-b border-slate-200/50 bg-white/40 px-4 py-3 sm:px-6">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Quick actions</p>
        {chips && chips.length > 0 && onChip && (
          <div className="mt-2">
            <QuickActions chips={chips} onSelect={onChip} />
          </div>
        )}
      </div>
      <div className="flex min-h-0 flex-1 flex-col">
        <div
          className="shrink-0 border-b border-slate-100 bg-slate-50/40 px-4 py-2 sm:px-6"
          role="region"
          aria-label="Conversation"
        >
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Conversation</span>
        </div>
        <ChatMessages
          messages={messages}
          typing={typing}
          bottomRef={bottomRef}
          connecting={connecting}
        />
        {voiceBar}
        <ChatComposer value={input} onChange={onInputChange} onSend={onSend} disabled={disabled} />
        {embeddedContent ? (
          <div
            className="max-h-[min(45vh,420px)] shrink-0 space-y-4 overflow-y-auto border-t border-slate-200/60 bg-gradient-to-b from-slate-50/50 to-white/0 px-4 py-4 sm:px-5"
            role="region"
            aria-label="Scheduling and actions"
          >
            <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">In-chat scheduling</p>
            {embeddedContent}
          </div>
        ) : null}
      </div>
    </div>
  );
}
