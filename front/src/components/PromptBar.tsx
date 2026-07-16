"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles } from "lucide-react";
import { useConfiguratorStore } from "@/store/configurator-store";
import messages from "@/i18n/messages";

const placeholderExamples: Record<string, string[]> = {
  en: [
    "Gaming PC for 1440p, budget 6000 PLN",
    "Streaming and gaming rig under 7000 zł",
    "Silent workstation for 3D rendering",
    "Budget PC for competitive FPS games",
    "4K video editing build, max 10000 PLN",
  ],
  ru: [
    "Комп для монтажа 4K, бюджет 8000 zł",
    "Игровой ПК для 1440p, до 6000 PLN",
    "Тихая рабочая станция для рендеринга",
    "Бюджетный ПК для киберспорта",
    "Стриминг + игры, бюджет 7000 zł",
  ],
  uk: [
    "Комп для монтажу 4K, бюджет 8000 zł",
    "Ігровий ПК для 1440p, до 6000 PLN",
    "Тиха робоча станція для рендерингу",
    "Бюджетний ПК для кіберспорту",
    "Стримінг + ігри, бюджет 7000 zł",
  ],
  pl: [
    "Komputer do montażu 4K, budżet 8000 zł",
    "PC gamingowy na 1440p, do 6000 PLN",
    "Cicha stacja robocza do renderowania",
    "Budżetowy PC do gier kompetytywnych",
    "Streaming + gry, budżet 7000 zł",
  ],
};

const promptSuggestions: Record<string, string[]> = {
  en: [
    "Cyberpunk 2077 in 4K + OBS streaming",
    "Blender + DaVinci 4K, silent",
    "CS2 500 FPS on 1440p 240Hz",
    "Home AI server + gaming",
  ],
  ru: [
    "Cyberpunk 2077 в 4K + стриминг в OBS",
    "Blender + DaVinci 4K, тихий",
    "CS2 500 FPS на 1440p 240Hz",
    "Домашний AI сервер + gaming",
  ],
  uk: [
    "Cyberpunk 2077 в 4K + стрімінг в OBS",
    "Blender + DaVinci 4K, тихий",
    "CS2 500 FPS на 1440p 240Hz",
    "Домашній AI сервер + gaming",
  ],
  pl: [
    "Cyberpunk 2077 w 4K + streaming w OBS",
    "Blender + DaVinci 4K, cichy",
    "CS2 500 FPS na 1440p 240Hz",
    "Domowy serwer AI + gaming",
  ],
};

type PlaceholderAnimation = {
  language: string;
  text: string;
  exampleIndex: number;
  charIndex: number;
  isDeleting: boolean;
};

function initialAnimation(language: string): PlaceholderAnimation {
  return {
    language,
    text: "",
    exampleIndex: 0,
    charIndex: 0,
    isDeleting: false,
  };
}

export default function PromptBar() {
  const language = useConfiguratorStore((s) => s.language);
  const isLoading = useConfiguratorStore((s) => s.isLoading);
  const triggerGenerate = useConfiguratorStore((s) => s.triggerGenerate);
  const t = messages[language];

  const [inputValue, setInputValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [animation, setAnimation] = useState<PlaceholderAnimation>(() =>
    initialAnimation(language)
  );
  const inputRef = useRef<HTMLInputElement>(null);

  // Typewriter effect
  const examples = placeholderExamples[language] ?? placeholderExamples.en;
  const currentSuggestions = promptSuggestions[language] ?? promptSuggestions.en;
  const activeAnimation =
    animation.language === language ? animation : initialAnimation(language);
  const animatedPlaceholder = activeAnimation.text;

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
    setIsFocused(true);
    inputRef.current?.focus();
  };

  useEffect(() => {
    if (inputValue) return; // Don't animate if user is typing

    const currentExample = examples[activeAnimation.exampleIndex % examples.length];
    const atEnd =
      !activeAnimation.isDeleting &&
      activeAnimation.charIndex >= currentExample.length;
    const delay = atEnd ? 2000 : activeAnimation.isDeleting ? 25 : 50;

    const timeout = setTimeout(() => {
      setAnimation((previous) => {
        const current =
          previous.language === language ? previous : initialAnimation(language);
        const example = examples[current.exampleIndex % examples.length];

        if (!current.isDeleting && current.charIndex < example.length) {
          const nextCharIndex = current.charIndex + 1;
          return {
            ...current,
            charIndex: nextCharIndex,
            text: example.slice(0, nextCharIndex),
          };
        }

        if (!current.isDeleting) {
          return { ...current, isDeleting: true };
        }

        if (current.charIndex > 0) {
          const nextCharIndex = current.charIndex - 1;
          return {
            ...current,
            charIndex: nextCharIndex,
            text: example.slice(0, nextCharIndex),
          };
        }

        return {
          ...current,
          isDeleting: false,
          exampleIndex: (current.exampleIndex + 1) % examples.length,
        };
      });
    }, delay);

    return () => clearTimeout(timeout);
  }, [activeAnimation, examples, inputValue, language]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (isLoading) return;
      void triggerGenerate(inputValue || animatedPlaceholder);
    },
    [animatedPlaceholder, inputValue, isLoading, triggerGenerate]
  );

  return (
    <motion.section
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
      className="relative flex flex-col items-center px-4 pb-12 pt-20 sm:pt-28 md:pt-32"
    >
      {/* Background accent glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-0 h-[500px] w-[800px] -translate-x-1/2 rounded-full bg-[#6366f1]/[0.07] blur-[120px]" />
      </div>

      {/* Subtitle chip */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4, duration: 0.5 }}
        className="mb-6 flex items-center gap-2 rounded-full border border-[#6366f1]/20 bg-[#6366f1]/[0.08] px-4 py-1.5"
      >
        <Sparkles className="h-3.5 w-3.5 text-[#8b5cf6]" />
        <span className="text-xs font-medium tracking-wide text-[#a78bfa]">
          {t.header.subtitle}
        </span>
      </motion.div>

      {/* Heading */}
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="mb-3 text-center text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl"
      >
        <span className="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
          {t.header.title}
        </span>
      </motion.h2>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.65, duration: 0.5 }}
        className="mb-10 text-center text-sm text-zinc-500 sm:text-base"
      >
        {t.header.subtitle}
      </motion.p>

      {/* Prompt input */}
      <form onSubmit={handleSubmit} className="relative w-full max-w-2xl">
        {/* Animated gradient border */}
        <motion.div
          className="absolute -inset-[1px] rounded-2xl opacity-0"
          animate={{
            opacity: isFocused ? 1 : 0,
          }}
          transition={{ duration: 0.3 }}
        >
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#6366f1] via-[#8b5cf6] to-[#6366f1] bg-[length:200%_100%] animate-[shimmer_3s_linear_infinite]" />
        </motion.div>

        {/* Subtle static border when not focused */}
        <div
          className={`absolute -inset-[1px] rounded-2xl transition-opacity duration-300 ${
            isFocused ? "opacity-0" : "opacity-100"
          }`}
        >
          <div className="h-full w-full rounded-2xl bg-gradient-to-r from-white/[0.08] via-white/[0.04] to-white/[0.08]" />
        </div>

        {/* Input container */}
        <div className="relative flex items-center gap-3 rounded-2xl bg-[#0f0f18]/90 px-5 py-4 backdrop-blur-xl sm:py-5">
          <input
            id="prompt-input"
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={animatedPlaceholder || "..."}
            disabled={isLoading}
            aria-label="Prompt input for AI"
            className="min-w-0 flex-1 bg-transparent text-sm text-white placeholder-zinc-600 outline-none sm:text-base"
          />

          {/* Submit button */}
          <motion.button
            type="submit"
            disabled={isLoading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label="Generate build"
            className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#06b6d4] to-[#0284c7] text-white shadow-lg shadow-cyan-500/25 transition-all hover:shadow-cyan-500/40 disabled:opacity-50 sm:h-11 sm:w-11"
          >
            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div
                  key="loader"
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  exit={{ opacity: 0, rotate: 90 }}
                  transition={{ duration: 0.2 }}
                >
                  <Loader2 className="h-5 w-5 animate-spin" />
                </motion.div>
              ) : (
                <motion.div
                  key="send"
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  exit={{ opacity: 0, rotate: 90 }}
                  transition={{ duration: 0.2 }}
                >
                  <Send className="h-4.5 w-4.5 sm:h-5 sm:w-5" />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Button glow */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-[#06b6d4] to-[#0284c7] opacity-0 blur-xl transition-opacity hover:opacity-40" />
          </motion.button>
        </div>
      </form>

      {/* Loading state message */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="mt-6 flex items-center gap-2.5"
          >
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="h-1.5 w-1.5 rounded-full bg-[#06b6d4]"
                  animate={{
                    y: [0, -6, 0],
                    opacity: [0.4, 1, 0.4],
                  }}
                  transition={{
                    duration: 0.8,
                    repeat: Infinity,
                    delay: i * 0.15,
                    ease: "easeInOut",
                  }}
                />
              ))}
            </div>
            <span className="text-sm text-zinc-400">{t.prompt.loading}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Suggestions */}
      {!isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="mt-5 flex flex-wrap items-center justify-center gap-2 sm:justify-start"
        >
          <span className="text-xs text-zinc-500 font-medium mr-1">
            {language === 'ru' ? 'Попробуй:' : language === 'en' ? 'Try:' : language === 'uk' ? 'Спробуй:' : 'Spróbuj:'}
          </span>
          {currentSuggestions.map((sug, idx) => (
            <button
              key={idx}
              onClick={() => handleSuggestionClick(sug)}
              className="px-3 py-1.5 rounded-full border border-white/5 bg-white/[0.02] text-xs text-zinc-400 hover:text-[#06b6d4] hover:bg-white/[0.04] hover:border-[#06b6d4]/30 transition-all duration-200"
            >
              {sug}
            </button>
          ))}
        </motion.div>
      )}
    </motion.section>
  );
}
