"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Monitor,
  Keyboard,
  Shield,
  Mouse,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import peripherals, { Peripheral } from "@/data/peripherals";
import { useConfiguratorStore } from "@/store/configurator-store";
import messages from "@/i18n/messages";

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  monitor: Monitor,
  keyboard: Keyboard,
  ups: Shield,
  mouse: Mouse,
};

const CATEGORY_COLORS: Record<string, string> = {
  monitor: "#6366f1",
  keyboard: "#f59e0b",
  ups: "#22c55e",
  mouse: "#ec4899",
};

export default function UpsellSection() {
  const { language } = useConfiguratorStore();
  const t = messages[language];

  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const checkScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
  }, []);

  useEffect(() => {
    checkScroll();
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", checkScroll, { passive: true });
    window.addEventListener("resize", checkScroll);
    return () => {
      el.removeEventListener("scroll", checkScroll);
      window.removeEventListener("resize", checkScroll);
    };
  }, [checkScroll]);

  const scroll = (dir: "left" | "right") => {
    const el = scrollRef.current;
    if (!el) return;
    const amount = el.clientWidth * 0.7;
    el.scrollBy({ left: dir === "left" ? -amount : amount, behavior: "smooth" });
  };

  return (
    <section className="relative py-12 px-4 sm:px-6 lg:px-8">
      {/* ── Header ──────────────────────────────────── */}
      <div className="max-w-6xl mx-auto mb-8">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-2xl sm:text-3xl font-bold tracking-tight"
        >
          <span className="bg-gradient-to-r from-[#6366f1] via-[#8b5cf6] to-[#a78bfa] bg-clip-text text-transparent">
            {t.upsell.title}
          </span>
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.08 }}
          className="mt-1.5 text-sm text-gray-500"
        >
          {t.upsell.subtitle}
        </motion.p>
      </div>

      {/* ── Scroll container ────────────────────────── */}
      <div className="relative max-w-6xl mx-auto">
        {/* Left button */}
        {canScrollLeft && (
          <button
            onClick={() => scroll("left")}
            className="absolute -left-2 sm:-left-4 md:-left-8 top-1/2 -translate-y-1/2 z-20
                       w-10 h-10 rounded-full flex items-center justify-center
                       bg-[#13131f]/90 border border-white/10 backdrop-blur-sm
                       text-gray-300 hover:text-white hover:border-[#6366f1]/40
                       shadow-lg transition-all duration-200"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        )}

        {/* Right button */}
        {canScrollRight && (
          <button
            onClick={() => scroll("right")}
            className="absolute -right-2 sm:-right-4 md:-right-8 top-1/2 -translate-y-1/2 z-20
                       w-10 h-10 rounded-full flex items-center justify-center
                       bg-[#13131f]/90 border border-white/10 backdrop-blur-sm
                       text-gray-300 hover:text-white hover:border-[#6366f1]/40
                       shadow-lg transition-all duration-200"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        )}

        {/* Left/Right fade edges */}
        {canScrollLeft && (
          <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-12 z-10 bg-gradient-to-r from-[#0b111a] to-transparent" />
        )}
        {canScrollRight && (
          <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-12 z-10 bg-gradient-to-l from-[#0b111a] to-transparent" />
        )}

        {/* Cards row */}
        <div
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto snap-x snap-mandatory
                     scrollbar-none pb-2 -mx-1 px-1"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {peripherals.map((p, idx) => (
            <PeripheralCard key={p.id} peripheral={p} language={language} index={idx} buyLabel={t.upsell.buyAt} />
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Single Card ──────────────────────────────────────── */

function PeripheralCard({
  peripheral,
  language,
  index,
  buyLabel,
}: {
  peripheral: Peripheral;
  language: string;
  index: number;
  buyLabel: string;
}) {
  const Icon = CATEGORY_ICONS[peripheral.category] ?? Monitor;
  const accent = CATEGORY_COLORS[peripheral.category] ?? "#6366f1";
  const description =
    peripheral.description[language] ?? peripheral.description.en;
  const tag = peripheral.tag[language] ?? peripheral.tag.en;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      className="group relative snap-start shrink-0 w-[280px] sm:w-[300px]
                 rounded-2xl overflow-hidden
                 border border-white/[0.07] bg-white/[0.03] backdrop-blur-md
                 hover:border-transparent
                 transition-all duration-300 ease-out
                 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(99,102,241,0.12)]"
    >
      {/* Gradient border on hover (via pseudo-like approach with bg) */}
      <div
        className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `linear-gradient(135deg, ${accent}33, transparent 60%, #8b5cf633)`,
        }}
      />

      <div className="relative p-5 flex flex-col h-full min-h-[260px]">
        {/* Icon + Tag row */}
        <div className="flex items-start justify-between mb-4">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${accent}18` }}
          >
            <Icon className="w-5 h-5" style={{ color: accent }} />
          </div>

          <span
            className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full"
            style={{
              backgroundColor: `${accent}18`,
              color: accent,
            }}
          >
            {tag}
          </span>
        </div>

        {/* Name */}
        <h3 className="text-sm font-semibold text-white leading-snug mb-2 line-clamp-2">
          {peripheral.name}
        </h3>

        {/* Description */}
        <p className="text-xs text-gray-400 leading-relaxed mb-4 line-clamp-3 flex-1">
          {description}
        </p>

        {/* Price + CTA */}
        <div className="flex items-center justify-between mt-auto pt-3 border-t border-white/[0.06]">
          <span className="text-lg font-bold text-white">
            {peripheral.price.toLocaleString("pl-PL")}{" "}
            <span className="text-xs font-normal text-gray-500">zł</span>
          </span>

          <a
            href={peripheral.shopUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold
                       bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] text-white
                       hover:shadow-[0_0_20px_rgba(99,102,241,0.35)] hover:scale-[1.03]
                       active:scale-[0.98] transition-all duration-200"
          >
            {buyLabel} X-Kom
            <ExternalLink className="w-3 h-3 opacity-70" />
          </a>
        </div>
      </div>
    </motion.div>
  );
}
