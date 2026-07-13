"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Heart, Trash2, ChevronRight, Clock } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { useConfiguratorStore } from "@/store/configurator-store";

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "short", year: "numeric" });
}

function formatPrice(price: number): string {
  return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0") + " zł";
}

export default function SavedBuildsDrawer() {
  const { savedBuildsOpen, closeSavedBuilds, savedBuilds, removeSavedBuild } = useAuthStore();

  return (
    <AnimatePresence>
      {savedBuildsOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            key="drawer-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeSavedBuilds}
            className="fixed inset-0 z-[55] bg-black/50 backdrop-blur-sm"
          />

          {/* Drawer */}
          <motion.aside
            key="drawer"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
            className="fixed right-0 top-0 bottom-0 z-[56] w-full max-w-sm border-l border-white/[0.06] bg-[#0b111a] shadow-2xl overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
              <div className="flex items-center gap-2.5">
                <Heart className="w-4 h-4 text-[#06b6d4]" />
                <h2 className="text-sm font-semibold text-white">Сохранённые сборки</h2>
                {savedBuilds.length > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-[#06b6d4]/20 text-[#06b6d4] text-xs font-bold">
                    {savedBuilds.length}
                  </span>
                )}
              </div>
              <button
                onClick={closeSavedBuilds}
                aria-label="Close"
                className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto py-3 px-4 space-y-3">
              {savedBuilds.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col items-center justify-center h-48 gap-3 text-center"
                >
                  <Heart className="w-10 h-10 text-white/10" />
                  <p className="text-sm text-zinc-500">Нет сохранённых сборок</p>
                  <p className="text-xs text-zinc-600">
                    Нажмите ♡ на сборке, чтобы сохранить её здесь
                  </p>
                </motion.div>
              ) : (
                <AnimatePresence initial={false}>
                  {savedBuilds.map((sb) => (
                    <motion.div
                      key={sb.id}
                      layout
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: 60 }}
                      transition={{ duration: 0.2 }}
                      className="group rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-[#06b6d4]/20 p-4 transition-all cursor-pointer"
                    >
                      {/* Build name + badge */}
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-white truncate">{sb.name}</p>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <Clock className="w-3 h-3 text-zinc-600" />
                            <span className="text-[10px] text-zinc-600">
                              {formatDate(sb.savedAt)}
                            </span>
                          </div>
                        </div>
                        <div
                          className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide"
                          style={{
                            background: `${sb.build.badge.color}22`,
                            color: sb.build.badge.color,
                            border: `1px solid ${sb.build.badge.color}44`,
                          }}
                        >
                          {sb.build.badge.label["ru"] ?? sb.build.badge.label["en"]}
                        </div>
                      </div>

                      {/* Price + components preview */}
                      <p className="text-lg font-bold text-[#06b6d4] mb-2">
                        {formatPrice(sb.build.totalPrice)}
                      </p>
                      <div className="flex flex-wrap gap-1 mb-3">
                        {Object.values(sb.build.components)
                          .slice(0, 3)
                          .map((c) => (
                            <span
                              key={c.id}
                              className="text-[10px] bg-white/[0.04] text-zinc-400 rounded-full px-2 py-0.5 truncate max-w-[120px]"
                            >
                              {c.name}
                            </span>
                          ))}
                        {Object.values(sb.build.components).length > 3 && (
                          <span className="text-[10px] text-zinc-600 px-1">
                            +{Object.values(sb.build.components).length - 3}
                          </span>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            useConfiguratorStore.getState().loadSavedBuild?.(sb.build);
                            closeSavedBuilds();
                          }}
                          className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-[#06b6d4]/10 hover:bg-[#06b6d4]/20 border border-[#06b6d4]/20 text-[#06b6d4] text-xs font-semibold py-2 transition-all"
                        >
                          Открыть <ChevronRight className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removeSavedBuild(sb.id);
                          }}
                          aria-label="Delete saved build"
                          className="p-2 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
