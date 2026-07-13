"use client";

import { motion } from "framer-motion";
import { Cpu, Sparkles } from "lucide-react";

type AppMode = "configurator" | "ai";

type ModeSliderProps = {
  mode: AppMode;
  onChange: (mode: AppMode) => void;
};

const modes: { id: AppMode; label: string; icon: React.ReactNode }[] = [
  {
    id: "configurator",
    label: "Конфигуратор",
    icon: <Cpu className="w-3.5 h-3.5" />,
  },
  {
    id: "ai",
    label: "ИИ-подбор",
    icon: <Sparkles className="w-3.5 h-3.5" />,
  },
];

export default function ModeSlider({ mode, onChange }: ModeSliderProps) {
  return (
    <div className="flex items-center gap-1 rounded-xl border border-white/[0.06] bg-white/[0.03] p-1">
      {modes.map((m) => {
        const isActive = mode === m.id;
        return (
          <motion.button
            key={m.id}
            onClick={() => onChange(m.id)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            aria-pressed={isActive}
            className={`relative flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              isActive ? "text-white" : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="modeSlider"
                className="absolute inset-0 rounded-lg bg-gradient-to-r from-[#06b6d4]/80 to-[#0ea5e9]/80 shadow-lg shadow-cyan-500/20"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10">{m.icon}</span>
            <span className="relative z-10 hidden sm:inline">{m.label}</span>
          </motion.button>
        );
      })}
    </div>
  );
}
