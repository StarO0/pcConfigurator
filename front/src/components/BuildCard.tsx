"use client";

import { motion } from "framer-motion";
import type { Build } from "@/data/builds";
import { CATEGORY_ORDER } from "@/data/builds";
import { useConfiguratorStore } from "@/store/configurator-store";

import ComponentCell from "@/components/ComponentCell";

/* ── Props ────────────────────────────────────────────────────── */
type BuildCardProps = {
  build: Build;
  buildIndex: number;
};



/* ── Component ────────────────────────────────────────────────── */
export default function BuildCard({ build, buildIndex }: BuildCardProps) {
  const openReplaceModal = useConfiguratorStore((s) => s.openReplaceModal);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full flex flex-col gap-3"
    >
      {CATEGORY_ORDER.map((cat) => {
        const comp = build.components[cat];
        return (
          <ComponentCell
            key={cat}
            component={comp}
            category={cat}
            onReplace={() => openReplaceModal(cat)}
          />
        );
      })}
    </motion.div>
  );
}
