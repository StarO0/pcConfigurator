"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Brain } from "lucide-react";
import { useConfiguratorStore } from "@/store/configurator-store";
import messages from "@/i18n/messages";

/* ── Props ────────────────────────────────────────────────────── */
type AiExplanationProps = {
  explanation: Record<string, string>;
  language: string;
};

/* ── Component ────────────────────────────────────────────────── */
export default function AiExplanation({
  explanation,
  language,
}: AiExplanationProps) {
  const t = messages[language as keyof typeof messages] ?? messages.en;

  const fullText = explanation[language] ?? explanation.en ?? "";
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* Reset + start typing whenever text or language changes */
  useEffect(() => {
    setDisplayed("");
    setDone(false);

    if (!fullText) return;

    let index = 0;
    intervalRef.current = setInterval(() => {
      index += 1;
      if (index >= fullText.length) {
        setDisplayed(fullText);
        setDone(true);
        if (intervalRef.current) clearInterval(intervalRef.current);
        return;
      }
      setDisplayed(fullText.slice(0, index));
    }, 18);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fullText, language]);

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={language + fullText.slice(0, 30)}
        initial={{ opacity: 0, x: -16 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 16 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="relative overflow-hidden rounded-2xl border border-white/[0.06]
                   bg-white/[0.03] backdrop-blur-xl"
      >
        {/* ── Gradient accent bar (left edge) ─────────────────── */}
        <div
          className="absolute inset-y-0 left-0 w-1 rounded-l-2xl
                     bg-gradient-to-b from-cyan-500 to-teal-500"
        />

        <div className="p-5 pl-6 sm:p-6 sm:pl-7">
          {/* ── Title row ──────────────────────────────────────── */}
          <div className="mb-3 flex items-center gap-2.5">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-lg
                          bg-gradient-to-br from-indigo-500/20 to-violet-500/20
                          text-indigo-400"
            >
              <Brain className="h-4.5 w-4.5" />
            </div>

            <h3 className="flex items-center gap-1.5 text-sm font-bold text-white/90">
              {t.build.aiExplanation}
              <Sparkles className="h-3.5 w-3.5 text-violet-400 opacity-70" />
            </h3>
          </div>

          {/* ── Typing body ────────────────────────────────────── */}
          <p className="text-sm leading-relaxed text-white/60">
            {displayed}
            {!done && (
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  repeatType: "reverse",
                }}
                className="ml-0.5 inline-block h-4 w-[2px] translate-y-[2px]
                           rounded-full bg-indigo-400"
              />
            )}
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
