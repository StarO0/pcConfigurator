"use client";

import { Bell, Boxes, Database, GitCompareArrows, WandSparkles } from "lucide-react";
import { useWorkspaceStore, type WorkspaceSection } from "@/store/workspace-store";

const ITEMS: Array<{ id: WorkspaceSection; label: string; icon: typeof Boxes }> = [
  { id: "builder", label: "Конфигуратор", icon: WandSparkles },
  { id: "catalog", label: "Каталог товаров", icon: Boxes },
  { id: "compare", label: "Сравнение", icon: GitCompareArrows },
  { id: "account", label: "Избранное и алерты", icon: Bell },
  { id: "data", label: "Данные", icon: Database },
];

export default function WorkspaceNav() {
  const { section, setSection } = useWorkspaceStore();
  return (
    <nav className="border-b border-white/[0.06] bg-[#080d14]/90" aria-label="Разделы проекта">
      <div className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-4 py-2 sm:px-6 lg:px-8">
        {ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            data-testid={`nav-${id}`}
            onClick={() => setSection(id)}
            className={`flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold transition sm:text-sm ${
              section === id
                ? "bg-cyan-500/15 text-cyan-300 ring-1 ring-cyan-400/30"
                : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-200"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>
    </nav>
  );
}
