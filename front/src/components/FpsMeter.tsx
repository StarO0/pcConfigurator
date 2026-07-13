"use client";

import { useState } from "react";
import { AnimatePresence, motion, useMotionValue, useTransform, animate } from "framer-motion";
import { Gamepad2, Briefcase, Monitor, Settings } from "lucide-react";
import benchmarks from "@/data/benchmarks";
import messages from "@/i18n/messages";
import { useConfiguratorStore } from "@/store/configurator-store";
import { useEffect, useRef } from "react";

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

/* ─── main component ─── */
export function FpsMeter({ buildId }: { buildId: string }) {
  const language = useConfiguratorStore((s) => s.language);
  const t = messages[language];
  const data = benchmarks[buildId];
  const [tab, setTab] = useState<"gaming" | "work">("gaming");

  if (!data) return null;

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
      </div>
    </div>
  );
}
