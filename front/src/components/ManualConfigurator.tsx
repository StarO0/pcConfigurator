"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Cpu, Monitor, MemoryStick, HardDrive, CircuitBoard,
  Zap, Box, Fan, ChevronDown, X, Heart, Check
} from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { useConfiguratorStore } from "@/store/configurator-store";
import type { Component, ComponentCategory } from "@/data/builds";
import { COMPONENT_LABELS } from "@/data/builds";
import { api, mapComponent, type ApiCompatibility } from "@/lib/api";
import PowerBadge from "@/components/PowerBadge";

const CATEGORY_ICONS: Record<ComponentCategory, React.ReactNode> = {
  cpu: <Cpu className="w-4 h-4" />,
  gpu: <Monitor className="w-4 h-4" />,
  ram: <MemoryStick className="w-4 h-4" />,
  ssd: <HardDrive className="w-4 h-4" />,
  motherboard: <CircuitBoard className="w-4 h-4" />,
  psu: <Zap className="w-4 h-4" />,
  case: <Box className="w-4 h-4" />,
  cooler: <Fan className="w-4 h-4" />,
};

const CATEGORIES: ComponentCategory[] = [
  "cpu", "gpu", "ram", "ssd", "motherboard", "psu", "case", "cooler"
];

const API_CATEGORIES: Record<ComponentCategory, string> = {
  cpu: "cpu",
  gpu: "gpu",
  ram: "ram",
  ssd: "storage",
  motherboard: "motherboard",
  psu: "psu",
  case: "case",
  cooler: "cooler",
};

function emptyOptions(): Record<ComponentCategory, Component[]> {
  return { cpu: [], gpu: [], ram: [], ssd: [], motherboard: [], psu: [], case: [], cooler: [] };
}

function formatPLN(v: number) {
  return v.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0") + " zł";
}

export default function ManualConfigurator() {
  const { isLoggedIn, openAuthModal, ensureAccessToken, refreshSavedBuilds } = useAuthStore();
  const language = useConfiguratorStore((state) => state.language);
  const [selected, setSelected] = useState<Partial<Record<ComponentCategory, Component>>>({});
  const [openDropdown, setOpenDropdown] = useState<ComponentCategory | null>(null);
  const [componentOptions, setComponentOptions] = useState(emptyOptions);
  const [loadedCategories, setLoadedCategories] = useState<Set<ComponentCategory>>(new Set());
  const [loadingCategory, setLoadingCategory] = useState<ComponentCategory | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [compatibility, setCompatibility] = useState<ApiCompatibility | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [savedMessage, setSavedMessage] = useState(false);

  const totalPrice = Object.values(selected).reduce((sum, c) => sum + (c?.price ?? 0), 0);
  const totalWatts = Object.values(selected).reduce((sum, c) => sum + (c?.wattage ?? 0), 0);
  const selectedCount = Object.keys(selected).length;

  useEffect(() => {
    const ids = Object.fromEntries(
      Object.entries(selected).map(([category, component]) => [
        API_CATEGORIES[category as ComponentCategory],
        component.id,
      ]),
    );
    const timeout = window.setTimeout(() => {
      if (!Object.keys(ids).length) {
        setCompatibility(null);
        return;
      }
      void api.compatibility(ids, language).then(setCompatibility).catch(() => setCompatibility(null));
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [language, selected]);

  async function loadCategory(category: ComponentCategory) {
    if (loadedCategories.has(category)) return;
    setLoadingCategory(category);
    setCatalogError("");
    try {
      const response = await api.products({
        category: API_CATEGORIES[category],
        inStock: true,
        sort: "price",
        limit: 200,
      });
      const options = response.items.map((product) =>
        mapComponent(category, product, product.offers.find((offer) => offer.in_stock) ?? null),
      );
      setComponentOptions((current) => ({ ...current, [category]: options }));
      setLoadedCategories((current) => new Set(current).add(category));
    } catch (reason) {
      setCatalogError(reason instanceof Error ? reason.message : "Не удалось загрузить каталог");
    } finally {
      setLoadingCategory(null);
    }
  }

  function toggleCategory(category: ComponentCategory) {
    const next = openDropdown === category ? null : category;
    setOpenDropdown(next);
    if (next) void loadCategory(category);
  }

  function handleSelect(cat: ComponentCategory, comp: Component) {
    setSelected((prev) => ({ ...prev, [cat]: comp }));
    setOpenDropdown(null);
  }

  function handleRemove(cat: ComponentCategory) {
    setSelected((prev) => {
      const next = { ...prev };
      delete next[cat];
      return next;
    });
  }

  async function handleSave() {
    if (!isLoggedIn) {
      openAuthModal("login");
      return;
    }
    setSaving(true);
    setSaveError("");
    try {
      const token = await ensureAccessToken();
      if (!token) return;
      const components = Object.fromEntries(
        Object.entries(selected).map(([category, component]) => [
          API_CATEGORIES[category as ComponentCategory],
          component.id,
        ]),
      );
      await api.createManualBuild(
        components,
        `Своя сборка — ${formatPLN(totalPrice)}`,
        language,
        token,
      );
      await refreshSavedBuilds();
      setSavedMessage(true);
      window.setTimeout(() => setSavedMessage(false), 2500);
    } catch (reason) {
      setSaveError(reason instanceof Error ? reason.message : "Не удалось сохранить сборку");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h2 className="text-2xl font-bold text-white mb-1">Ручной конфигуратор</h2>
        <p className="text-sm text-zinc-500">Реальные товары и цены из локальной базы с проверкой совместимости</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Component selectors */}
        <div className="lg:col-span-2 space-y-3">
          {CATEGORIES.map((cat, idx) => {
            const sel = selected[cat];
            const isOpen = openDropdown === cat;
            const options = componentOptions[cat];

            return (
              <motion.div
                key={cat}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="relative"
              >
                {/* Category row */}
                <div
                  className={`rounded-xl border transition-all ${
                    isOpen
                      ? "border-[#06b6d4]/40 bg-[#06b6d4]/5"
                      : sel
                      ? "border-white/[0.1] bg-white/[0.03]"
                      : "border-white/[0.06] bg-white/[0.02]"
                  }`}
                >
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => toggleCategory(cat)}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") toggleCategory(cat); }}
                    className="w-full flex items-center gap-3 px-4 py-3.5 text-left cursor-pointer outline-none"
                  >
                    <span
                      className={`flex-shrink-0 ${
                        sel ? "text-[#06b6d4]" : "text-zinc-600"
                      }`}
                    >
                      {CATEGORY_ICONS[cat]}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">
                        {COMPONENT_LABELS[cat].ru}
                      </p>
                      {sel ? (
                        <p className="text-sm font-medium text-white truncate">{sel.name}</p>
                      ) : (
                        <p className="text-sm text-zinc-600">Не выбрано</p>
                      )}
                    </div>
                    {sel ? (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-[#06b6d4]">{formatPLN(sel.price)}</span>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleRemove(cat); }}
                          aria-label="Remove"
                          className="p-1 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <ChevronDown
                        className={`w-4 h-4 text-zinc-600 transition-transform ${
                          isOpen ? "rotate-180" : ""
                        }`}
                      />
                    )}
                  </div>

                  {/* Dropdown */}
                  <AnimatePresence>
                    {isOpen && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden border-t border-white/[0.06]"
                      >
                        <div className="py-2 max-h-60 overflow-y-auto">
                          {loadingCategory === cat ? (
                            <p className="text-sm text-cyan-400 px-4 py-2">Загружаем реальные предложения…</p>
                          ) : options.length === 0 ? (
                            <p className="text-sm text-zinc-600 px-4 py-2">Нет товаров с импортированной ценой</p>
                          ) : (
                            options.map((comp) => (
                              <button
                                key={comp.id}
                                onClick={() => handleSelect(cat, comp)}
                                className={`w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/[0.04] transition-colors ${
                                  sel?.id === comp.id ? "bg-[#06b6d4]/10" : ""
                                }`}
                              >
                                <div className="text-left">
                                  <p className="text-sm text-white">{comp.name}</p>
                                  {comp.specs && (
                                    <p className="text-[11px] text-zinc-500 mt-0.5">
                                      {Object.entries(comp.specs)
                                        .slice(0, 3)
                                        .map(([, v]) => `${v}`)
                                        .join(" · ")}
                                    </p>
                                  )}
                                </div>
                                <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                                  <span className="text-sm font-bold text-[#06b6d4]">
                                    {formatPLN(comp.price)}
                                  </span>
                                  {sel?.id === comp.id && (
                                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                                  )}
                                </div>
                              </button>
                            ))
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Right: Summary sidebar */}
        <div className="lg:col-span-1">
          <motion.div
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="sticky top-20 rounded-2xl border border-white/[0.06] bg-white/[0.03] p-5"
          >
            <h3 className="text-sm font-semibold text-white mb-4">Итоговая сборка</h3>

            {/* Progress */}
            <div className="mb-4">
              <div className="flex justify-between text-xs text-zinc-500 mb-1.5">
                <span>Комплектующих выбрано</span>
                <span className="text-white font-medium">{selectedCount} / {CATEGORIES.length}</span>
              </div>
              <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-[#06b6d4] to-[#0ea5e9] rounded-full"
                  animate={{ width: `${(selectedCount / CATEGORIES.length) * 100}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>
            </div>

            {/* Price */}
            <div className="mb-3">
              <p className="text-xs text-zinc-500 mb-0.5">Итого</p>
              <p className="text-2xl font-bold text-[#06b6d4]">{formatPLN(totalPrice)}</p>
            </div>

            {/* Power */}
            {totalWatts > 0 && <PowerBadge watts={totalWatts} />}

            {compatibility && (
              <div className={`mt-4 rounded-xl border p-3 text-xs ${
                compatibility.status === "incompatible"
                  ? "border-red-500/20 bg-red-500/10 text-red-300"
                  : compatibility.status === "warning"
                    ? "border-amber-500/20 bg-amber-500/10 text-amber-300"
                    : "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
              }`}>
                <p className="font-semibold">
                  {compatibility.status === "compatible" ? "Совместимость подтверждена" : compatibility.status === "warning" ? "Есть предупреждения" : "Компоненты несовместимы"}
                </p>
                <p className="mt-1 opacity-80">Пик: ~{compatibility.estimated_peak_power_w} Вт{compatibility.recommended_psu_w ? ` · БП от ${compatibility.recommended_psu_w} Вт` : ""}</p>
                {compatibility.issues.slice(0, 3).map((issue) => <p key={issue.code} className="mt-1">• {issue.message}</p>)}
              </div>
            )}

            {catalogError && <p className="mt-3 text-xs text-red-400">{catalogError}</p>}

            {/* Save button */}
            <div className="mt-4">
              <AnimatePresence mode="wait">
                {savedMessage ? (
                  <motion.div
                    key="saved"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold"
                  >
                    <Check className="w-4 h-4" />
                    Сохранено!
                  </motion.div>
                ) : (
                  <motion.button
                    key="save"
                    onClick={() => void handleSave()}
                    disabled={selectedCount < 4 || saving || compatibility?.status === "incompatible"}
                    whileHover={{ scale: selectedCount >= 4 && compatibility?.status !== "incompatible" ? 1.02 : 1 }}
                    whileTap={{ scale: selectedCount >= 4 && compatibility?.status !== "incompatible" ? 0.98 : 1 }}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-[#06b6d4] to-[#0ea5e9] text-white text-sm font-semibold shadow-lg shadow-cyan-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  >
                    <Heart className="w-4 h-4" />
                    {saving ? "Сохраняем…" : isLoggedIn ? "Сохранить сборку" : "Войдите для сохранения"}
                  </motion.button>
                )}
              </AnimatePresence>
            </div>

            {selectedCount < 4 && (
              <p className="text-[11px] text-zinc-600 text-center mt-2">
                Выберите минимум 4 компонента для сохранения
              </p>
            )}
            {saveError && <p className="mt-2 text-center text-xs text-red-400">{saveError}</p>}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
