"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, X } from "lucide-react";
import { useConfiguratorStore } from "@/store/configurator-store";
import messages from "@/i18n/messages";

export function BottleneckWarning() {
  const bottleneckWarning = useConfiguratorStore((s) => s.bottleneckWarning);
  const dismissBottleneck = useConfiguratorStore((s) => s.dismissBottleneck);
  const language = useConfiguratorStore((s) => s.language);
  const t = messages[language];

  return (
    <AnimatePresence>
      {bottleneckWarning && (
        <motion.div
          initial={{ opacity: 0, y: -40, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -40, scale: 0.97 }}
          transition={{ type: "spring", stiffness: 380, damping: 28 }}
          className="w-full max-w-4xl mx-auto px-4 mb-4"
        >
          {/* outer pulsing border container */}
          <div className="relative rounded-2xl p-[1px] overflow-hidden">
            {/* animated gradient border */}
            <div
              className="absolute inset-0 rounded-2xl"
              style={{
                background:
                  "linear-gradient(135deg, #ef4444, #f97316, #ef4444, #f97316)",
                backgroundSize: "300% 300%",
                animation: "bottleneck-pulse 2.5s ease-in-out infinite",
              }}
            />

            {/* inner card */}
            <div className="relative rounded-2xl bg-[#0d0d14]/95 backdrop-blur-2xl p-5 md:p-6">
              <div className="flex items-start gap-4">
                {/* icon */}
                <div className="flex-shrink-0 mt-0.5">
                  <motion.div
                    animate={{
                      scale: [1, 1.15, 1],
                      rotate: [0, -8, 8, 0],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                    className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500/20 to-orange-500/20 border border-red-500/30 flex items-center justify-center"
                  >
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                  </motion.div>
                </div>

                {/* text */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-sm font-bold text-red-400 uppercase tracking-wide">
                      {t.bottleneck.warning}
                    </h4>
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                    </span>
                  </div>

                  <p className="text-sm text-white/70 leading-relaxed">
                    {bottleneckWarning.type === "cpu"
                      ? t.bottleneck.cpuLimits
                      : t.bottleneck.gpuLimits}{" "}
                    <span className="font-bold text-orange-400">
                      {bottleneckWarning.percentage}%
                    </span>
                  </p>

                  <p className="mt-2 text-sm text-white/50">
                    {t.bottleneck.recommend}{" "}
                    <span className="font-semibold bg-gradient-to-r from-violet-400 to-blue-400 bg-clip-text text-transparent">
                      {bottleneckWarning.recommendation}
                    </span>
                  </p>
                </div>

                {/* dismiss */}
                <button
                  onClick={dismissBottleneck}
                  aria-label="Dismiss"
                  className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
                             border border-white/[0.06] bg-white/[0.04]
                             text-white/40 hover:text-white hover:bg-white/[0.1]
                             transition-all duration-200 active:scale-90"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* keyframes injected via global style */}
          <style dangerouslySetInnerHTML={{ __html: `
            @keyframes bottleneck-pulse {
              0%, 100% { background-position: 0% 50%; opacity: 0.7; }
              50% { background-position: 100% 50%; opacity: 1; }
            }
          `}} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
