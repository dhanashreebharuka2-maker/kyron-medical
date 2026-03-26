"use client";

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { ChatComposer } from "./ChatComposer";
import { ChatHeader } from "./ChatHeader";
import type { ChatLine } from "./ChatMessages";
import { ChatMessages } from "./ChatMessages";
import { QuickActions } from "./QuickActions";

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
  connecting?: boolean;
};

export function ChatShell({
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
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing, embedSignature]);

  return (
    <div className="flex max-h-[min(56rem,calc(100vh-10rem))] flex-col overflow-hidden rounded-3xl border border-slate-200/60 bg-gradient-to-b from-white/95 via-white/90 to-sky-50/50 shadow-xl backdrop-blur-2xl">
      {/* Header — Quick options */}
      <div className="shrink-0 border-b border-slate-200/50 bg-white/40 px-4 py-3 sm:px-6">
        <ChatHeader />
        <p className="mt-3 text-[11px] font-medium uppercase tracking-wide text-slate-500">
          Quick options
        </p>
        {chips && chips.length > 0 && onChip && (
          <div className="mt-2">
            <QuickActions chips={chips} onSelect={onChip} />
          </div>
        )}
        <p className="mt-2 text-xs text-slate-400">
          You can also type freely in <strong>Chat</strong> at the bottom.
        </p>
      </div>

      {/* Conversation section */}
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="shrink-0 border-b border-slate-100 bg-slate-50/40 px-4 py-2 sm:px-6">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Conversation
          </span>
        </div>
        <ChatMessages
          messages={messages}
          typing={typing}
          bottomRef={bottomRef}
          connecting={connecting}
        />
      </div>

      {/* Chat input section */}
      <div className="shrink-0 border-t border-slate-200/60 bg-white/80 px-4 pb-4 pt-3 sm:px-6">
        <div className="mb-2 flex items-center gap-1.5">
          <svg className="h-3.5 w-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Chat</span>
        </div>
        <label htmlFor="chat-input" className="sr-only">
          Write your message here
        </label>
        <ChatComposer
          value={input}
          onChange={onInputChange}
          onSend={onSend}
          disabled={disabled}
        />
        <p id="chat-hint" className="mt-1 text-xs text-slate-400">
          Press Enter or Send — same assistant as the buttons above.
        </p>
      </div>

      {/* Embedded scheduling content (intake, slots, etc.) */}
      {embeddedContent && (
        <div
          className="max-h-[min(45vh,420px)] shrink-0 space-y-4 overflow-y-auto border-t border-slate-200/60 bg-gradient-to-b from-slate-50/50 to-white/0 px-4 py-4 sm:px-5"
          role="region"
          aria-label="Location and next steps"
        >
          <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Location &amp; next steps
          </p>
          {embeddedContent}
        </div>
      )}
    </div>
  );
}
