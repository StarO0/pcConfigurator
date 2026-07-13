"use client";

import { motion } from "framer-motion";
import { Cpu, User, LogOut, Heart } from "lucide-react";
import { useConfiguratorStore } from "@/store/configurator-store";
import { useAuthStore } from "@/store/auth-store";
import messages, { Language } from "@/i18n/messages";
import ModeSlider from "./ModeSlider";

const languages: { code: Language; flag: string; label: string }[] = [
  { code: "en", flag: "🇬🇧", label: "EN" },
  { code: "ru", flag: "🇷🇺", label: "RU" },
  { code: "uk", flag: "🇺🇦", label: "UK" },
  { code: "pl", flag: "🇵🇱", label: "PL" },
];

export default function Header() {
  const { language, setLanguage, appMode, setAppMode } = useConfiguratorStore();
  const { user, isLoggedIn, openAuthModal, openSavedBuilds, logout } = useAuthStore();
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

          {/* Center: Mode Slider */}
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 hidden md:block">
            <ModeSlider mode={appMode} onChange={setAppMode} />
          </div>

          {/* Right side: Language + Account */}
          <div className="flex items-center gap-3">
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

            {/* Account Button */}
            {isLoggedIn ? (
              <div className="relative group">
                <button
                  onClick={openSavedBuilds}
                  className="flex items-center justify-center gap-2 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3 py-2 text-sm font-semibold text-white hover:bg-white/[0.06] hover:border-white/[0.1] transition-all"
                >
                  <User className="w-4 h-4 text-[#06b6d4]" />
                  <span className="hidden sm:inline truncate max-w-[100px]">{user?.displayName}</span>
                </button>
                <div className="absolute right-0 top-full mt-2 w-48 opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity z-50">
                  <div className="rounded-xl border border-white/[0.06] bg-[#0f1520]/95 backdrop-blur-xl p-1.5 shadow-2xl">
                    <button
                      onClick={openSavedBuilds}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-white hover:bg-white/[0.04] transition-colors"
                    >
                      <Heart className="w-4 h-4 text-[#06b6d4]" />
                      Сохранённые сборки
                    </button>
                    <div className="h-px w-full bg-white/[0.06] my-1" />
                    <button
                      onClick={logout}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Выйти
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <button
                onClick={() => openAuthModal("login")}
                className="flex items-center justify-center rounded-xl bg-[#06b6d4]/10 hover:bg-[#06b6d4]/20 border border-[#06b6d4]/20 px-4 py-2 text-sm font-semibold text-[#06b6d4] transition-all"
              >
                Войти
              </button>
            )}
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
