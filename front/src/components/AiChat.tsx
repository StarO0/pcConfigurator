"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles, Bot, User, RotateCcw } from "lucide-react";
import { useChatStore } from "@/store/chat-store";
import { useConfiguratorStore } from "@/store/configurator-store";

const SUGGESTIONS = [
  "Игровой ПК для 1440p, бюджет 5000 zł",
  "Тихая рабочая станция для рендеринга",
  "CS2 500 FPS на 1440p 240Hz",
  "Мощный ПК для монтажа 4K",
];

export default function AiChat() {
  const { messages, phase, sendMessage, clearChat } = useChatStore();
  const showResults = useConfiguratorStore((s) => s.showResults);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || phase === "generating") return;
    sendMessage(content);
    setInput("");
    inputRef.current?.focus();
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // IDLE state — hero input
  if (phase === "idle") {
    return (
      <section className="flex flex-col items-center justify-center px-4 py-12 w-full">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-[#06b6d4]/20 bg-[#06b6d4]/10 px-4 py-1.5 mb-5">
            <Sparkles className="w-3.5 h-3.5 text-[#06b6d4]" />
            <span className="text-xs font-semibold text-[#06b6d4]">ИИ-конфигуратор</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">
            Опишите{" "}
            <span className="bg-gradient-to-r from-[#06b6d4] to-[#0ea5e9] bg-clip-text text-transparent">
              идеальный ПК
            </span>
          </h2>
          <p className="text-zinc-500 text-sm max-w-md mx-auto">
            ИИ задаст уточняющие вопросы и подберёт 5 оптимальных сборок под ваши задачи и бюджет
          </p>
        </motion.div>

        {/* Input */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="w-full max-w-2xl"
        >
          <div className="relative">
            <div className="absolute -inset-[1px] rounded-2xl bg-gradient-to-r from-[#06b6d4]/50 via-[#0ea5e9]/30 to-[#06b6d4]/50 opacity-0 group-focus-within:opacity-100 transition-opacity" />
            <div className="relative flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-[#0f1520]/90 px-5 py-4 backdrop-blur-xl">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Например: игровой ПК для 1440p, бюджет 6000 zł..."
                className="flex-1 bg-transparent text-sm text-white placeholder-zinc-600 outline-none"
              />
              <motion.button
                onClick={() => handleSend()}
                disabled={!input.trim()}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                aria-label="Send message"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#06b6d4] to-[#0ea5e9] text-white shadow-lg shadow-cyan-500/25 disabled:opacity-40 transition-all"
              >
                <Send className="h-4 w-4" />
              </motion.button>
            </div>
          </div>

          {/* Suggestions */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-4 flex flex-wrap items-center justify-center gap-2"
          >
            <span className="text-xs text-zinc-500 font-medium mr-1">Попробуй:</span>
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSend(s)}
                className="px-3 py-1.5 rounded-full border border-white/5 bg-white/[0.02] text-xs text-zinc-400 hover:text-[#06b6d4] hover:bg-white/[0.04] hover:border-[#06b6d4]/30 transition-all duration-200"
              >
                {s}
              </button>
            ))}
          </motion.div>
        </motion.div>
      </section>
    );
  }

  // CHAT state (clarifying / generating / chatting)
  return (
    <section className="w-full max-w-2xl mx-auto px-4 flex flex-col">
      {/* Chat header */}
      <div className="flex items-center justify-between py-3 mb-2">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#06b6d4]/20 to-[#0ea5e9]/20 border border-[#06b6d4]/30 flex items-center justify-center">
            <Bot className="w-4 h-4 text-[#06b6d4]" />
          </div>
          <span className="text-sm font-semibold text-white">ИИ-консультант</span>
          {phase === "generating" && (
            <span className="flex items-center gap-1 text-xs text-[#06b6d4]">
              <Loader2 className="w-3 h-3 animate-spin" />
              генерирует...
            </span>
          )}
        </div>
        <button
          onClick={clearChat}
          className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-white transition-colors px-2 py-1 rounded-lg hover:bg-white/[0.05]"
        >
          <RotateCcw className="w-3 h-3" />
          Начать заново
        </button>
      </div>

      {/* Messages */}
      <div className="space-y-3 mb-4 min-h-[120px]">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              className={`flex gap-2.5 ${
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              {/* Avatar */}
              <div
                className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center mt-0.5 ${
                  msg.role === "ai"
                    ? "bg-gradient-to-br from-[#06b6d4]/20 to-[#0ea5e9]/20 border border-[#06b6d4]/30"
                    : "bg-white/[0.08] border border-white/[0.08]"
                }`}
              >
                {msg.role === "ai" ? (
                  <Bot className="w-4 h-4 text-[#06b6d4]" />
                ) : (
                  <User className="w-3.5 h-3.5 text-zinc-400" />
                )}
              </div>

              {/* Bubble */}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "ai"
                    ? "bg-white/[0.04] border border-white/[0.06] text-white/90 rounded-tl-none"
                    : "bg-gradient-to-br from-[#06b6d4]/20 to-[#0ea5e9]/20 border border-[#06b6d4]/20 text-white rounded-tr-none"
                }`}
              >
                {msg.isTyping ? (
                  <span className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <motion.span
                        key={i}
                        className="inline-block w-1.5 h-1.5 rounded-full bg-[#06b6d4]"
                        animate={{ y: [0, -4, 0] }}
                        transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
                      />
                    ))}
                  </span>
                ) : (
                  msg.content
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input (shown during clarifying / chatting phases) */}
      {(phase === "clarifying" || phase === "chatting") && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-[#0f1520]/90 px-4 py-3 backdrop-blur-xl"
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={
              phase === "clarifying"
                ? "Ответьте на вопрос ИИ..."
                : "Уточните пожелания (например: сделай дешевле, замени на AMD)..."
            }
            className="flex-1 bg-transparent text-sm text-white placeholder-zinc-600 outline-none"
          />
          <motion.button
            onClick={() => handleSend()}
            disabled={!input.trim()}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label="Send"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#06b6d4] to-[#0ea5e9] text-white disabled:opacity-40 transition-all"
          >
            <Send className="h-3.5 w-3.5" />
          </motion.button>
        </motion.div>
      )}
    </section>
  );
}
