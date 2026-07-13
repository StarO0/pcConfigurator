"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ArrowDownCircle, ArrowUpCircle, Check } from "lucide-react";
import { useConfiguratorStore } from "@/store/configurator-store";
import alternatives from "@/data/alternatives";
import peripherals from "@/data/peripherals";
import { COMPONENT_LABELS, Component, AllCategory } from "@/data/builds";
import messages from "@/i18n/messages";

type Tab = "cheaper" | "upgrade";

export default function ReplaceModal() {
  const {
    replaceModalOpen,
    replaceCategory,
    closeReplaceModal,
    replaceComponent,
    currentBuildIndex,
    builds,
    language,
  } = useConfiguratorStore();

  const [activeTab, setActiveTab] = useState<Tab>("cheaper");

  const t = messages[language];
  const currentBuild = builds[currentBuildIndex];

  if (!replaceModalOpen || !replaceCategory) return null;

  const isPeripheral = ["monitor", "keyboard", "mouse", "ups"].includes(replaceCategory);
  const categoryAlternatives = alternatives[replaceCategory as keyof typeof alternatives] || { cheaper: [], upgrade: [] };
  const currentComponent = currentBuild.components[replaceCategory as keyof typeof currentBuild.components];
  const currentPrice = currentComponent?.price ?? 0;
  
  const categoryLabel =
    COMPONENT_LABELS[replaceCategory as AllCategory]?.[language] ??
    COMPONENT_LABELS[replaceCategory as AllCategory]?.en ??
    replaceCategory;

  let items: Component[] = [];
  if (isPeripheral) {
    items = peripherals
      .filter((p) => p.category === replaceCategory)
      .map((p) => ({
        id: p.id,
        category: p.category as any,
        name: p.name,
        price: p.price,
        shopLinks: [{ shop: "Store", url: p.shopUrl, price: p.price }],
        specs: { Info: p.description[language] ?? p.description.en },
      }));
  } else {
    items = activeTab === "cheaper"
      ? categoryAlternatives.cheaper
      : categoryAlternatives.upgrade;
  }

  const handleSelect = (component: Component) => {
    replaceComponent(currentBuildIndex, replaceCategory as any, component);
  };

  return (
    <AnimatePresence>
      {replaceModalOpen && (
        <motion.div
          key="replace-backdrop"
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-md"
            onClick={closeReplaceModal}
          />

          {/* Modal */}
          <motion.div
            key="replace-modal"
            className="relative z-10 w-full max-w-lg max-h-[85vh] flex flex-col
                       rounded-t-2xl sm:rounded-2xl overflow-hidden
                       border border-white/10
                       bg-gradient-to-b from-[#0b111a]/95 to-[#05080f]/95
                       shadow-[0_0_80px_rgba(6,182,212,0.12)]"
            initial={{ y: 80, opacity: 0, scale: 0.97 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 80, opacity: 0, scale: 0.97 }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
          >
            {/* ── Header ─────────────────────────────── */}
            <div className="flex items-center justify-between px-6 pt-5 pb-3">
              <h2 className="text-lg font-semibold text-white tracking-tight">
                {currentComponent ? t.replace.title : (t.component?.add ?? "Dodaj")}:{" "}
                <span className="bg-gradient-to-r from-[#06b6d4] to-[#0891b2] bg-clip-text text-transparent">
                  {categoryLabel}
                </span>
              </h2>
              <button
                onClick={closeReplaceModal}
                aria-label="Close"
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors group"
              >
                <X className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
              </button>
            </div>

            {/* ── Current Component ──────────────────── */}
            {currentComponent && (
              <div className="px-6 mb-2">
                <div className="rounded-xl border border-[#06b6d4]/20 bg-[#06b6d4]/[0.02] p-4">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <h3 className="text-xs font-semibold text-[#06b6d4] uppercase tracking-wider mb-1">
                        {t.replace.currentComponent}
                      </h3>
                      <p className="text-sm font-semibold text-white">
                        {currentComponent.name}
                      </p>
                    </div>
                    <span className="text-base font-bold text-white shrink-0">
                      {currentPrice.toLocaleString("pl-PL")} zł
                    </span>
                  </div>

                  {/* Specs badges */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {Object.entries(currentComponent.specs).map(([key, value]) => (
                      <span
                        key={key}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium
                                   bg-white/[0.06] text-gray-300 border border-white/[0.05]"
                      >
                        <span className="text-gray-500 mr-1 uppercase tracking-wider text-[9px]">
                          {key}
                        </span>
                        {value}
                      </span>
                    ))}
                  </div>

                  {/* Shop Links */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {currentComponent.shopLinks.map((link) => (
                      <a
                        key={link.shop}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex flex-col items-center justify-center py-2 px-3 rounded-lg
                                   bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.05]
                                   hover:border-[#06b6d4]/30 transition-all duration-200 group"
                      >
                        <span className="text-[11px] font-medium text-gray-400 group-hover:text-gray-300 mb-0.5 transition-colors">
                          {link.shop}
                        </span>
                        <span className="text-xs font-bold text-[#06b6d4]">
                          {link.price.toLocaleString("pl-PL")} zł
                        </span>
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── Tabs ───────────────────────────────── */}
            {!isPeripheral && (
              <div className="flex px-6 gap-1">
                {(["cheaper", "upgrade"] as const).map((tab) => {
                  const isActive = activeTab === tab;
                  const label =
                    tab === "cheaper" ? t.replace.cheaperTab : t.replace.upgradeTab;
                  const Icon = tab === "cheaper" ? ArrowDownCircle : ArrowUpCircle;

                  return (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`relative flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-colors
                        ${isActive ? "text-white" : "text-gray-500 hover:text-gray-300"}`}
                    >
                      <Icon className="w-4 h-4" />
                      {label}

                      {/* Gradient underline */}
                      {isActive && (
                        <motion.div
                          layoutId="tab-underline"
                          className="absolute -bottom-px left-3 right-3 h-[2px] rounded-full
                                     bg-gradient-to-r from-[#06b6d4] to-[#0891b2]"
                          transition={{ type: "spring", damping: 30, stiffness: 400 }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Add a line if tabs or component existed */}
            {(!isPeripheral || currentComponent) && (
              <div className="mx-6 h-px bg-white/[0.06] mt-0.5" />
            )}

            {/* ── List ───────────────────────────────── */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 scrollbar-thin scrollbar-thumb-white/10">
              {items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                  <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
                    <X className="w-5 h-5" />
                  </div>
                  <p className="text-sm">No alternatives available</p>
                </div>
              ) : (
                items.map((alt, idx) => {
                  const diff = alt.price - currentPrice;
                  const isCheaper = diff < 0;

                  return (
                    <motion.div
                      key={alt.id}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.06, duration: 0.3 }}
                      className="group relative rounded-xl border border-white/[0.07] bg-white/[0.03]
                                 hover:border-[#06b6d4]/30 hover:bg-white/[0.05]
                                 transition-all duration-200 p-4"
                    >
                      {/* Top: Name + Price */}
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-white truncate">
                            {alt.name}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-base font-bold text-white">
                              {alt.price.toLocaleString("pl-PL")} zł
                            </span>
                            {currentComponent && (
                              <span
                                className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                                  isCheaper
                                    ? "bg-emerald-500/15 text-emerald-400"
                                    : "bg-red-500/15 text-red-400"
                                }`}
                              >
                                {isCheaper ? "" : "+"}
                                {diff.toLocaleString("pl-PL")} zł
                              </span>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => handleSelect(alt)}
                          className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold
                                     bg-gradient-to-r from-[#06b6d4] to-[#0891b2] text-white
                                     hover:shadow-[0_0_20px_rgba(6,182,212,0.35)] hover:scale-[1.03]
                                     active:scale-[0.98] transition-all duration-200"
                        >
                          <Check className="w-3.5 h-3.5" />
                          {t.replace.select}
                        </button>
                      </div>

                      {/* Specs badges */}
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(alt.specs).map(([key, value]) => (
                          <span
                            key={key}
                            className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium
                                       bg-white/[0.06] text-gray-400 border border-white/[0.05]
                                       group-hover:border-white/10 transition-colors"
                          >
                            <span className="text-gray-500 mr-1 uppercase tracking-wider text-[9px]">
                              {key}
                            </span>
                            <span className="break-all md:break-normal line-clamp-2">{value}</span>
                          </span>
                        ))}
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
