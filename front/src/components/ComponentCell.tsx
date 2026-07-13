"use client";

import {
  Cpu,
  Monitor,
  MemoryStick,
  HardDrive,
  CircuitBoard,
  Zap,
  Box,
  Fan,
  ArrowLeftRight,
  Keyboard,
  Mouse,
  BatteryWarning,
  MonitorPlay,
  Plus,
  Sparkles
} from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Component, AllCategory } from "@/data/builds";
import { COMPONENT_LABELS } from "@/data/builds";
import { useConfiguratorStore } from "@/store/configurator-store";
import messages from "@/i18n/messages";
import type { ReactNode } from "react";

/* ── Icon map ─────────────────────────────────────────────────── */
const CATEGORY_ICONS: Record<AllCategory, ReactNode> = {
  cpu: <Cpu className="h-5 w-5" />,
  gpu: <Monitor className="h-5 w-5" />,
  ram: <MemoryStick className="h-5 w-5" />,
  ssd: <HardDrive className="h-5 w-5" />,
  motherboard: <CircuitBoard className="h-5 w-5" />,
  psu: <Zap className="h-5 w-5" />,
  case: <Box className="h-5 w-5" />,
  cooler: <Fan className="h-5 w-5" />,
  monitor: <MonitorPlay className="h-5 w-5" />,
  keyboard: <Keyboard className="h-5 w-5" />,
  mouse: <Mouse className="h-5 w-5" />,
  ups: <BatteryWarning className="h-5 w-5" />,
};

/* ── Helpers ──────────────────────────────────────────────────── */
function formatPLN(value: number): string {
  return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0") + " zł";
}

/* ── Props ────────────────────────────────────────────────────── */
type ComponentCellProps = {
  component?: Component;
  category: AllCategory;
  reason?: string;
  onReplace: () => void;
};

/* ── Component ────────────────────────────────────────────────── */
export default function ComponentCell({
  component,
  category,
  reason,
  onReplace,
}: ComponentCellProps) {
  const language = useConfiguratorStore((s) => s.language);
  const t = messages[language];
  const [showTooltip, setShowTooltip] = useState(false);

  const categoryLabel = COMPONENT_LABELS[category]?.[language] ?? category;

  if (!component) {
    return (
      <div
        className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-dashed border-[#1e293b]
                   bg-transparent p-4 transition-all duration-300
                   hover:border-indigo-500/40 hover:bg-[#131B26]/30"
      >
        <div className="flex flex-1 items-center gap-4 opacity-60 grayscale">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-slate-900 border border-slate-800 text-slate-500">
            {CATEGORY_ICONS[category]}
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              {categoryLabel}
            </span>
            <h3 className="mt-0.5 text-sm font-bold leading-tight text-slate-400">
              {t.component.notSelected}
            </h3>
          </div>
        </div>
        <div className="flex shrink-0 items-center justify-between sm:justify-end gap-4 w-full sm:w-auto mt-2 sm:mt-0">
          <button
            onClick={onReplace}
            className="flex items-center justify-center gap-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-xs font-semibold text-indigo-300 transition-all duration-200 hover:bg-indigo-500/20 active:scale-[0.97]"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>{t.component.add}</span>
          </button>
        </div>
      </div>
    );
  }

  const specEntries = Object.entries(component.specs).slice(0, 4);

  return (
    <div
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      className="group relative flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-[#1e293b]
                 bg-[#131B26]/80 p-4 backdrop-blur-xl transition-all duration-300
                 hover:border-indigo-500/40 hover:shadow-[0_0_24px_rgba(99,102,241,0.1)]"
    >
      <AnimatePresence>
        {showTooltip && reason && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-64 z-50 pointer-events-none"
          >
            <div className="relative rounded-xl border border-[#06b6d4]/30 bg-[#0f1520]/95 p-3 shadow-xl backdrop-blur-md">
              <div className="flex items-start gap-2">
                <Sparkles className="w-3.5 h-3.5 text-[#06b6d4] shrink-0 mt-0.5" />
                <p className="text-xs text-white/90 leading-relaxed">{reason}</p>
              </div>
              <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rotate-45 border-r border-b border-[#06b6d4]/30 bg-[#0f1520]/95" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-1 items-center gap-4">
        {/* ── Left side: Icon ───────────────────────────────────── */}
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-cyan-950/40 border border-cyan-900/50 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
          {CATEGORY_ICONS[category]}
        </div>

        {/* ── Middle: Info ──────────────────────────────────────── */}
        <div className="flex flex-col">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
            {categoryLabel}
          </span>
          <h3 className="mt-0.5 text-sm font-bold leading-tight text-white line-clamp-2">
            {component.name}
          </h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-400">
            {specEntries.map(([key, value]) => (
              <span key={key} className="flex items-center gap-1">
                <span className="text-slate-500">{key}:</span>
                <span className="font-medium text-slate-300">{value}</span>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right side: Price & Action ────────────────────────── */}
      <div className="flex shrink-0 items-center justify-between sm:justify-end gap-4 w-full sm:w-auto mt-2 sm:mt-0">
        <div className="text-left sm:text-right">
          <p className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            {formatPLN(component.price)}
          </p>
        </div>

        <button
          onClick={onReplace}
          className="flex items-center justify-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.04] px-4 py-2 text-xs font-semibold text-white/70 transition-all duration-200 hover:border-indigo-500/40 hover:bg-indigo-500/10 hover:text-indigo-300 active:scale-[0.97]"
        >
          <ArrowLeftRight className="h-3.5 w-3.5" />
          <span>{t.component.replace}</span>
        </button>
      </div>
    </div>
  );
}
