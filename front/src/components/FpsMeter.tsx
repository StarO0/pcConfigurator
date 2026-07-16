"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useMotionValue, useTransform, animate } from "framer-motion";
import { Gamepad2, Briefcase, Monitor, Settings, Loader2 } from "lucide-react";
import benchmarks from "@/data/benchmarks";
import type { BenchmarkData } from "@/data/benchmarks";
import type { Build } from "@/data/builds";
import messages from "@/i18n/messages";
import { api, type ApiBuildAnalysis } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { useConfiguratorStore } from "@/store/configurator-store";

/* ─── animated FPS counter ─── */
function AnimatedFps({ value }: { value: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const motionVal = useMotionValue(0);
  const rounded = useTransform(motionVal, (v) => Math.round(v));

  useEffect(() => {
    const controls = animate(motionVal, value, {
      duration: 1.2,
      ease: "easeOut",
    });
    const unsub = rounded.on("change", (latest) => {
      if (ref.current) ref.current.textContent = String(latest);
    });
    return () => {
      controls.stop();
      unsub();
    };
  }, [value, motionVal, rounded]);

  return <span ref={ref}>0</span>;
}

/* ─── FPS colour helper ─── */
function fpsColor(fps: number) {
  if (fps >= 100) return "from-emerald-400 to-green-300";
  if (fps >= 60) return "from-yellow-400 to-amber-300";
  return "from-orange-500 to-red-400";
}

function fpsGlow(fps: number) {
  if (fps >= 100) return "shadow-emerald-500/20";
  if (fps >= 60) return "shadow-yellow-500/20";
  return "shadow-orange-500/20";
}

const ANALYSIS_TEXT = {
  en: { loading: "Calculating performance…", unavailable: "Performance estimate is unavailable", api: "Local API estimate", demo: "Demo estimate" },
  ru: { loading: "Рассчитываем производительность…", unavailable: "Оценка производительности недоступна", api: "Расчёт локального API", demo: "Демонстрационная оценка" },
  uk: { loading: "Розраховуємо продуктивність…", unavailable: "Оцінка продуктивності недоступна", api: "Розрахунок локального API", demo: "Демонстраційна оцінка" },
  pl: { loading: "Obliczanie wydajności…", unavailable: "Ocena wydajności jest niedostępna", api: "Szacunek lokalnego API", demo: "Szacunek demonstracyjny" },
};

function mapAnalysis(analysis: ApiBuildAnalysis): BenchmarkData {
  return {
    gaming: analysis.performance
      .filter((entry) => entry.kind === "game")
      .map((entry) => ({
        game: entry.workload_name,
        resolution: entry.resolution ?? "—",
        fps: Math.round(entry.value),
        preset: entry.settings ?? entry.confidence,
      })),
    work: analysis.performance
      .filter((entry) => entry.kind !== "game")
      .map((entry) => ({
        task: entry.workload_name,
        time: `${entry.value.toLocaleString(undefined, { maximumFractionDigits: 1 })} ${entry.unit}`,
      })),
  };
}

/* ─── main component ─── */
export function FpsMeter({ build }: { build: Build }) {
  const language = useConfiguratorStore((s) => s.language);
  const accessToken = useAuthStore((s) => s.accessToken);
  const t = messages[language];
  const statusText = ANALYSIS_TEXT[language] ?? ANALYSIS_TEXT.en;
  const [analysis, setAnalysis] = useState<ApiBuildAnalysis | null>(null);
  const [analysisFailed, setAnalysisFailed] = useState(false);
  const [tab, setTab] = useState<"gaming" | "work">("gaming");

  useEffect(() => {
    if (!build.backendId) return;
    let active = true;
    void api
      .analysis(build, language, accessToken)
      .then((result) => {
        if (active) setAnalysis(result);
      })
      .catch(() => {
        if (active) setAnalysisFailed(true);
      });
    return () => {
      active = false;
    };
  }, [accessToken, build, language]);

  const data = analysis ? mapAnalysis(analysis) : benchmarks[build.id];

  if (build.backendId && !analysis && !analysisFailed) {
    return (
      <div className="flex min-h-40 items-center justify-center gap-2 rounded-2xl border border-white/[0.06] bg-white/[0.03] text-sm text-white/50">
        <Loader2 className="h-4 w-4 animate-spin" />
        {statusText.loading}
      </div>
    );
  }

  if (!data || (!data.gaming.length && !data.work.length)) {
    return (
      <div className="flex min-h-32 items-center justify-center rounded-2xl border border-white/[0.06] bg-white/[0.03] text-sm text-white/40">
        {statusText.unavailable}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-2xl overflow-hidden">
      {/* ─── header ─── */}
      <div className="px-6 pt-5 pb-0 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center shadow-lg shadow-violet-500/20">
          <Gamepad2 className="w-4 h-4 text-white" />
        </div>
        <h3 className="text-sm font-semibold text-white/90">
          {t.build.performance}
        </h3>
      </div>

      {/* ─── tabs ─── */}
      <div className="flex gap-1 mx-6 mt-4 p-1 rounded-xl bg-white/[0.04] border border-white/[0.06]">
        {(["gaming", "work"] as const).map((key) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`relative flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium transition-all duration-300 ${
              tab === key
                ? "text-white"
                : "text-white/40 hover:text-white/60"
            }`}
          >
            {tab === key && (
              <motion.span
                layoutId="fps-tab-bg"
                className="absolute inset-0 bg-gradient-to-r from-[#06b6d4]/20 to-[#2dd4bf]/20 rounded-md -z-10"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-1.5">
              {key === "gaming" ? (
                <Gamepad2 className="w-3.5 h-3.5" />
              ) : (
                <Briefcase className="w-3.5 h-3.5" />
              )}
              {key === "gaming" ? t.build.gaming : t.build.work}
            </span>
          </button>
        ))}
      </div>

      {/* ─── tab content ─── */}
      <div className="p-6 pt-5">
        <AnimatePresence mode="wait">
          {tab === "gaming" ? (
            <motion.div
              key="gaming"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
              className="grid gap-3"
            >
              {data.gaming.map((entry, i) => (
                <motion.div
                  key={entry.game}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className={`flex items-center justify-between gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 ${fpsGlow(entry.fps)}`}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-white/90 truncate">
                      {entry.game}
                    </p>
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className="flex items-center gap-1 text-[10px] text-white/40">
                        <Monitor className="w-3 h-3" />
                        {entry.resolution}
                      </span>
                      <span className="flex items-center gap-1 text-[10px] text-white/40">
                        <Settings className="w-3 h-3" />
                        {entry.preset}
                      </span>
                    </div>
                  </div>

                  {/* FPS counter */}
                  <div className="text-right flex-shrink-0">
                    <p
                      className={`text-2xl font-extrabold bg-gradient-to-r ${fpsColor(entry.fps)} bg-clip-text text-transparent tabular-nums`}
                    >
                      <AnimatedFps value={entry.fps} />
                    </p>
                    <p className="text-[10px] uppercase tracking-wider text-white/30 mt-0.5">
                      {t.build.fps}
                    </p>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <motion.div
              key="work"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
              className="grid gap-3"
            >
              {data.work.map((entry, i) => (
                <motion.div
                  key={entry.task}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="flex items-center justify-between gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 hover:border-white/[0.12] transition-colors"
                >
                  <p className="text-sm text-white/70 leading-snug flex-1 min-w-0">
                    {entry.task}
                  </p>
                  <p className="text-sm font-bold bg-gradient-to-r from-violet-400 to-blue-400 bg-clip-text text-transparent whitespace-nowrap">
                    {entry.time}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
        <p className="mt-4 text-center text-[10px] uppercase tracking-wider text-white/25">
          {analysis ? statusText.api : statusText.demo}
        </p>
      </div>
    </div>
  );
}
