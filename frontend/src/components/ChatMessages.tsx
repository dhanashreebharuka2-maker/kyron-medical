"use client";

import type { Ref, RefObject } from "react";
import { ChatMessage } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";

export type ChatLine = { role: "user" | "assistant"; content: string };

type Props = {
  messages: ChatLine[];
  typing?: boolean;
  bottomRef: RefObject<HTMLDivElement | null>;
  /** True while waiting for the first session / welcome message */
  connecting?: boolean;
};

export function ChatMessages({ messages, typing, bottomRef, connecting }: Props) {
  const showConnecting = Boolean(connecting) && messages.length === 0 && !typing;
  return (
    <div className="flex min-h-[12rem] flex-1 flex-col gap-4 overflow-y-auto px-4 py-4 sm:px-5">
      {showConnecting && (
        <p className="rounded-2xl border border-slate-200/80 bg-white/80 px-4 py-3 text-sm text-slate-600 shadow-sm">
          Connecting to the assistant…
        </p>
      )}
      {messages.map((m, i) => (
        <ChatMessage key={`${i}-${m.content.slice(0, 12)}`} role={m.role} content={m.content} />
      ))}
      {typing && <TypingIndicator />}
      <div ref={bottomRef as Ref<HTMLDivElement>} />
    </div>
  );
}
