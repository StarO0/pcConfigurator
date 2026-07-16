"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, ChevronLeft, ChevronRight, Check, Heart, XCircle } from "lucide-react";
import { useConfiguratorStore } from "@/store/configurator-store";
import { useAuthStore } from "@/store/auth-store";
import messages from "@/i18n/messages";
import { FpsMeter } from "@/components/FpsMeter";
import BuildCard from "@/components/BuildCard";
import PowerBadge from "@/components/PowerBadge";

/* ─── direction tracker (1 = forward, -1 = backward) ─── */
const slideVariants = {
  enter: (dir: number) => ({
    x: dir > 0 ? 420 : -420,
    opacity: 0,
    scale: 0.95,
  }),
  center: {
    x: 0,
    opacity: 1,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 300, damping: 30 },
  },
  exit: (dir: number) => ({
    x: dir > 0 ? -420 : 420,
    opacity: 0,
    scale: 0.95,
    transition: { duration: 0.25 },
  }),
};

export function BuildCarousel() {
  const {
    builds,
    currentBuildIndex,
    nextBuild,
    prevBuild,
    setCurrentBuild,
    language,
  } = useConfiguratorStore();
  const { saveBuild, isLoggedIn, openAuthModal } = useAuthStore();

  const t = messages[language];
  const [direction, setDirection] = useState(0);
  const [savedMessage, setSavedMessage] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const currentBuild = builds[currentBuildIndex];
  const compatibility = currentBuild.compatibilityStatus ?? "compatible";

  // Calculate total wattage
  const totalWatts = Object.values(currentBuild.components).reduce((sum, c) => sum + (c?.wattage ?? 0), 0);

  async function handleSave() {
    setSaveError(null);
    if (!isLoggedIn) {
      openAuthModal("login");
      return;
    }
    const name = `${currentBuild.badge.label[language]} — ${currentBuild.totalPrice.toLocaleString()} zł`;
    const result = await saveBuild(currentBuild, name);
    if (result.success) {
      setSavedMessage(true);
      setTimeout(() => setSavedMessage(false), 2500);
    } else {
      setSaveError(result.error ?? "Не удалось сохранить сборку");
    }
  }

  /* ─── navigation helpers ─── */
  const handlePrev = useCallback(() => {
    setDirection(-1);
    prevBuild();
  }, [prevBuild]);

  const handleNext = useCallback(() => {
    setDirection(1);
    nextBuild();
  }, [nextBuild]);

  const handleDot = useCallback(
    (idx: number) => {
      setDirection(idx > currentBuildIndex ? 1 : -1);
      setCurrentBuild(idx);
    },
    [currentBuildIndex, setCurrentBuild]
  );

  /* ─── keyboard navigation ─── */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handlePrev, handleNext]);

  return (
    <section className="relative w-full max-w-[80rem] mx-auto px-4 sm:px-12 md:px-24 py-8">
      {/* ─── main slide area ─── */}
      <div className="relative rounded-3xl min-h-[280px]">
        <AnimatePresence initial={false} custom={direction} mode="wait">
          <motion.div
            key={currentBuildIndex}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            className="w-full grid grid-cols-1 lg:grid-cols-3 gap-6"
          >
            {/* ── Left Column (Build Components) ── */}
            <div className="lg:col-span-2">
              <BuildCard build={currentBuild} />
            </div>

            {/* ── Right Column (Sidebar) ── */}
            <div className="lg:col-span-1">
              <div className="sticky top-24 flex flex-col gap-4">
                {/* 1. Summary Card */}
                <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-2xl p-6 shadow-[0_0_80px_rgba(99,102,241,0.08)]">
                  {/* Badge */}
                  <span
                    className="inline-block mb-4 px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase"
                    style={{
                      background: `${currentBuild.badge.color}22`,
                      color: currentBuild.badge.color,
                      border: `1px solid ${currentBuild.badge.color}44`,
                    }}
                  >
                    {currentBuild.badge.label[language]}
                  </span>

                  {/* Price */}
                  <div className="mb-4">
                    <p className="text-sm text-white/50 mb-1">{t.build.totalPrice}</p>
                    <p className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                      {currentBuild.totalPrice.toLocaleString()} zł
                    </p>
                  </div>

                  {/* Compatibility */}
                  <div
                    className={`flex items-center gap-2 mb-6 ${
                      compatibility === "compatible"
                        ? "text-emerald-400"
                        : compatibility === "warning"
                          ? "text-amber-400"
                          : "text-red-400"
                    }`}
                  >
                    <div className="flex items-center justify-center w-5 h-5 rounded-full bg-current/10">
                      {compatibility === "compatible" ? (
                        <Check className="w-3.5 h-3.5" strokeWidth={3} />
                      ) : compatibility === "warning" ? (
                        <AlertTriangle className="w-3.5 h-3.5" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <span className="text-sm font-medium">
                      {compatibility === "compatible"
                        ? "Kompatybilność OK"
                        : compatibility === "warning"
                          ? "Есть предупреждения совместимости"
                          : "Компоненты несовместимы"}
                    </span>
                  </div>

                  {/* Power Badge */}
                  {totalWatts > 0 && <PowerBadge watts={totalWatts} />}

                  {/* Button */}
                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={() => void useConfiguratorStore.getState().triggerGenerate()}
                      className="flex-1 py-3 px-4 rounded-xl font-bold text-white shadow-lg transition-all
                                 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400
                                 active:scale-95 flex items-center justify-center gap-2 text-sm"
                    >
                      {t.prompt.button} <ChevronRight className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={handleSave}
                      className="flex items-center justify-center w-12 rounded-xl bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.1] hover:border-pink-500/30 text-white/70 hover:text-pink-400 transition-all active:scale-95"
                      title="Сохранить сборку"
                    >
                      {savedMessage ? (
                        <Check className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <Heart className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {saveError && <p className="mt-2 text-xs text-red-400">{saveError}</p>}
                </div>

                {/* 2. FpsMeter */}
                <FpsMeter key={currentBuild.id} build={currentBuild} />

                {/* 3. AI Explanation */}
                <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-2xl p-6">
                  <h3 className="text-sm font-semibold text-violet-400 mb-2">
                    {t.build.aiExplanation}
                  </h3>
                  <p className="text-sm leading-relaxed text-white/60">
                    {currentBuild.aiExplanation[language]}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* ─── left arrow ─── */}
      <button
        onClick={handlePrev}
        aria-label={t.carousel.prev}
        className="absolute left-1 sm:left-4 md:left-8 top-1/2 -translate-y-1/2 z-20
                   w-10 h-10 md:w-14 md:h-14 rounded-full
                   flex items-center justify-center
                   border border-white/[0.08] bg-white/[0.04] backdrop-blur-xl
                   text-white/60 hover:text-white hover:bg-white/[0.1] hover:border-violet-500/30
                   transition-all duration-300 shadow-lg shadow-black/30
                   active:scale-90 hidden sm:flex"
      >
        <ChevronLeft className="w-6 h-6" />
      </button>

      {/* ─── right arrow ─── */}
      <button
        onClick={handleNext}
        aria-label={t.carousel.next}
        className="absolute right-1 sm:right-4 md:right-8 top-1/2 -translate-y-1/2 z-20
                   w-10 h-10 md:w-14 md:h-14 rounded-full
                   flex items-center justify-center
                   border border-white/[0.08] bg-white/[0.04] backdrop-blur-xl
                   text-white/60 hover:text-white hover:bg-white/[0.1] hover:border-violet-500/30
                   transition-all duration-300 shadow-lg shadow-black/30
                   active:scale-90 hidden sm:flex"
      >
        <ChevronRight className="w-6 h-6" />
      </button>

      {/* ─── dot indicators ─── */}
      <div className="flex items-center justify-center gap-2 mt-6">
        {builds.map((_, idx) => (
          <button
            key={idx}
            aria-label={`${idx + 1} ${t.carousel.of} ${builds.length}`}
            onClick={() => handleDot(idx)}
            className="group relative p-1"
          >
            <span
              className={`block rounded-full transition-all duration-300 ${
                idx === currentBuildIndex
                  ? "w-8 h-3 bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] shadow-[0_0_12px_rgba(139,92,246,0.5)]"
                  : "w-3 h-3 bg-white/15 group-hover:bg-white/30"
              }`}
            />
          </button>
        ))}
      </div>

      {/* ─── counter ─── */}
      <p className="text-center text-xs text-white/30 mt-2">
        {currentBuildIndex + 1} {t.carousel.of} {builds.length}
      </p>
    </section>
  );
}
