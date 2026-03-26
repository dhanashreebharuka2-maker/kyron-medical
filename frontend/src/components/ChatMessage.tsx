"use client";

import { motion } from "framer-motion";

type Props = {
  role: "user" | "assistant";
  content: string;
};

export function ChatMessage({ role, content }: Props) {
  const isUser = role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-glass ${
          isUser
            ? "bg-kyron-600 text-white"
            : "border border-white/40 bg-white/70 text-ink backdrop-blur-xl"
        }`}
      >
        {content}
      </div>
    </motion.div>
  );
}
