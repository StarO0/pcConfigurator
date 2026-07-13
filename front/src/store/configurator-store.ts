import { create } from "zustand";
import builds, { Build, Component, ComponentCategory, AllCategory } from "@/data/builds";
import { Language } from "@/i18n/messages";

// Simple bottleneck scores (higher = more powerful)
const cpuScores: Record<string, number> = {
  "cpu-r5-7500f": 55,
  "cpu-r7-9700x": 80,
  "cpu-r7-9800x3d": 95,
  "cpu-r9-9900x": 90,
  "cpu-i7-265k": 85,
  "alt-cpu-r5-7600": 58,
  "alt-cpu-i5-14400f": 52,
  "alt-cpu-r7-9800x3d": 95,
  "alt-cpu-r9-9900x": 90,
};

const gpuScores: Record<string, number> = {
  "gpu-rtx5070": 80,
  "gpu-rx7700xt": 65,
  "gpu-rtx5070ti": 90,
  "gpu-rx9070xt": 82,
  "gpu-rtx5070ti-intel": 90,
  "alt-gpu-rx7600": 45,
  "alt-gpu-rtx4060": 50,
  "alt-gpu-rtx5070ti": 90,
  "alt-gpu-rtx5080": 100,
};

export type BottleneckWarning = {
  type: "cpu" | "gpu";
  percentage: number;
  recommendation: string;
} | null;

type ConfiguratorState = {
  language: Language;
  builds: Build[];
  currentBuildIndex: number;
  showResults: boolean;
  isLoading: boolean;
  bottleneckWarning: BottleneckWarning;
  replaceModalOpen: boolean;
  replaceCategory: AllCategory | null;
  setLanguage: (lang: Language) => void;
  setCurrentBuild: (index: number) => void;
  nextBuild: () => void;
  prevBuild: () => void;
  replaceComponent: (buildIndex: number, category: AllCategory, component: Component) => void;
  openReplaceModal: (category: AllCategory) => void;
  closeReplaceModal: () => void;
  dismissBottleneck: () => void;
  triggerGenerate: () => void;
};

function calculateBottleneck(build: Build): BottleneckWarning {
  const cpuScore = cpuScores[build.components.cpu.id] ?? 70;
  const gpuScore = gpuScores[build.components.gpu.id] ?? 70;

  const diff = Math.abs(cpuScore - gpuScore);

  if (diff > 20) {
    if (cpuScore < gpuScore) {
      const pct = Math.round(((gpuScore - cpuScore) / gpuScore) * 100);
      return {
        type: "cpu",
        percentage: pct,
        recommendation: cpuScore < 60 ? "AMD Ryzen 7 9700X" : "AMD Ryzen 9 9900X",
      };
    } else {
      const pct = Math.round(((cpuScore - gpuScore) / cpuScore) * 100);
      return {
        type: "gpu",
        percentage: pct,
        recommendation: gpuScore < 60 ? "RTX 5070" : "RTX 5070 Ti",
      };
    }
  }

  return null;
}

export const useConfiguratorStore = create<ConfiguratorState>((set, get) => ({
  language: "en",
  builds: builds.map((b) => ({ ...b })),
  currentBuildIndex: 0,
  showResults: false,
  isLoading: false,
  bottleneckWarning: null,
  replaceModalOpen: false,
  replaceCategory: null,

  setLanguage: (lang) => set({ language: lang }),

  setCurrentBuild: (index) => set({ currentBuildIndex: index, bottleneckWarning: null }),

  nextBuild: () => {
    const { currentBuildIndex, builds } = get();
    set({
      currentBuildIndex: (currentBuildIndex + 1) % builds.length,
      bottleneckWarning: null,
    });
  },

  prevBuild: () => {
    const { currentBuildIndex, builds } = get();
    set({
      currentBuildIndex: (currentBuildIndex - 1 + builds.length) % builds.length,
      bottleneckWarning: null,
    });
  },

  replaceComponent: (buildIndex, category, component) => {
    const state = get();
    const newBuilds = [...state.builds];
    const build = { ...newBuilds[buildIndex] };
    build.components = { ...build.components, [category]: component };

    // Recalculate total price
    build.totalPrice = Object.values(build.components).reduce((sum, c) => sum + c.price, 0);

    newBuilds[buildIndex] = build;

    const warning = calculateBottleneck(build);

    set({
      builds: newBuilds,
      bottleneckWarning: warning,
      replaceModalOpen: false,
      replaceCategory: null,
    });
  },

  openReplaceModal: (category) =>
    set({ replaceModalOpen: true, replaceCategory: category }),

  closeReplaceModal: () =>
    set({ replaceModalOpen: false, replaceCategory: null }),

  dismissBottleneck: () => set({ bottleneckWarning: null }),

  triggerGenerate: () => {
    set({ isLoading: true });
    setTimeout(() => {
      set({ isLoading: false, showResults: true });
    }, 2000);
  },
}));
