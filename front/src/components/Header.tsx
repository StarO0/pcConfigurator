"use client";

import { motion } from "framer-motion";
import { Cpu } from "lucide-react";
import { useConfiguratorStore } from "@/store/configurator-store";
import messages, { Language } from "@/i18n/messages";

const languages: { code: Language; flag: string; label: string }[] = [
  { code: "en", flag: "🇬🇧", label: "EN" },
  { code: "ru", flag: "🇷🇺", label: "RU" },
  { code: "uk", flag: "🇺🇦", label: "UK" },
  { code: "pl", flag: "🇵🇱", label: "PL" },
];

export default function Header() {
  const language = useConfiguratorStore((s) => s.language);
  const setLanguage = useConfiguratorStore((s) => s.setLanguage);
  const t = messages[language];

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="sticky top-0 z-50 w-full"
    >
      {/* Glassmorphism background */}
      <div className="relative border-b border-white/[0.06] bg-[#0a0a0f]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Logo / Title */}
          <motion.div
            className="flex items-center gap-3"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] shadow-lg shadow-violet-500/25">
              <Cpu className="h-5 w-5 text-white" />
              {/* Icon glow */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] opacity-40 blur-lg" />
            </div>
            <h1 className="bg-gradient-to-r from-[#6366f1] via-[#8b5cf6] to-[#a78bfa] bg-clip-text text-lg font-bold tracking-tight text-transparent sm:text-xl">
              {t.header.title}
            </h1>
          </motion.div>

          {/* Language Switcher */}
          <div className="flex items-center gap-1 rounded-xl border border-white/[0.06] bg-white/[0.03] p-1">
            {languages.map((lang) => {
              const isActive = language === lang.code;
              return (
                <motion.button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`relative flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors sm:px-3 ${
                    isActive
                      ? "text-white"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {/* Active indicator background */}
                  {isActive && (
                    <motion.div
                      layoutId="activeLang"
                      className="absolute inset-0 rounded-lg bg-gradient-to-r from-[#6366f1]/80 to-[#8b5cf6]/80 shadow-lg shadow-violet-500/20"
                      transition={{
                        type: "spring",
                        stiffness: 400,
                        damping: 30,
                      }}
                    />
                  )}
                  <span className="relative z-10 text-sm">{lang.flag}</span>
                  <span className="relative z-10 hidden sm:inline">
                    {lang.label}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Bottom border glow */}
        <div className="absolute bottom-0 left-0 right-0 h-px">
          <div className="mx-auto h-full w-2/3 bg-gradient-to-r from-transparent via-[#6366f1]/50 to-transparent" />
        </div>
      </div>
    </motion.header>
  );
}
