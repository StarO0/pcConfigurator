import { create } from "zustand";
import type { Build, Component, ComponentCategory, AllCategory } from "@/data/builds";
import { Language } from "@/i18n/messages";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

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
  appMode: "configurator" | "ai";
  builds: Build[];
  currentBuildIndex: number;
  showResults: boolean;
  isLoading: boolean;
  generationError: string | null;
  lastPrompt: string;
  bottleneckWarning: BottleneckWarning;
  replaceModalOpen: boolean;
  replaceCategory: AllCategory | null;
  replacementOptions: Component[];
  replacementLoading: boolean;
  replacementError: string | null;
  setLanguage: (lang: Language) => void;
  setAppMode: (mode: "configurator" | "ai") => void;
  setCurrentBuild: (index: number) => void;
  nextBuild: () => void;
  prevBuild: () => void;
  replaceComponent: (buildIndex: number, category: AllCategory, component: Component) => Promise<void>;
  openReplaceModal: (category: AllCategory) => void;
  closeReplaceModal: () => void;
  dismissBottleneck: () => void;
  triggerGenerate: (prompt?: string) => Promise<void>;
  loadSavedBuild: (build: Build) => void;
};

function calculateBottleneck(build: Build): BottleneckWarning {
  if (build.bottleneck) {
    if (build.bottleneck.status === "balanced") return null;
    return {
      type: build.bottleneck.status === "cpu_limited" ? "cpu" : "gpu",
      percentage: Math.round(build.bottleneck.estimatedPercent),
      recommendation: build.bottleneck.recommendedProduct ?? build.bottleneck.message,
    };
  }

  const cpu = build.components.cpu;
  const gpu = build.components.gpu;
  if (!cpu || !gpu) return null;
  const cpuScore = cpuScores[cpu.id] ?? 70;
  const gpuScore = gpuScores[gpu.id] ?? 70;

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
  appMode: "configurator" as const,
  builds: [],
  currentBuildIndex: 0,
  showResults: false,
  isLoading: false,
  generationError: null,
  lastPrompt: "",
  bottleneckWarning: null,
  replaceModalOpen: false,
  replaceCategory: null,
  replacementOptions: [],
  replacementLoading: false,
  replacementError: null,

  setLanguage: (lang) => set({ language: lang }),
  setAppMode: (mode) => set({ appMode: mode }),

  setCurrentBuild: (index) => {
    const build = get().builds[index];
    if (build) set({ currentBuildIndex: index, bottleneckWarning: calculateBottleneck(build) });
  },

  nextBuild: () => {
    const { currentBuildIndex, builds } = get();
    if (!builds.length) return;
    const index = (currentBuildIndex + 1) % builds.length;
    set({ currentBuildIndex: index, bottleneckWarning: calculateBottleneck(builds[index]) });
  },

  prevBuild: () => {
    const { currentBuildIndex, builds } = get();
    if (!builds.length) return;
    const index = (currentBuildIndex - 1 + builds.length) % builds.length;
    set({ currentBuildIndex: index, bottleneckWarning: calculateBottleneck(builds[index]) });
  },

  replaceComponent: async (buildIndex, category, component) => {
    const state = get();
    const newBuilds = [...state.builds];
    let build = { ...newBuilds[buildIndex] };
    if (build.backendId && !["monitor", "keyboard", "mouse", "ups"].includes(category)) {
      try {
        const token = await useAuthStore.getState().ensureAccessToken();
        build = await api.replaceComponent(
          build,
          category as ComponentCategory,
          component,
          token,
        );
      } catch (error) {
        set({
          replacementError: error instanceof Error ? error.message : "Не удалось заменить компонент",
        });
        return;
      }
    } else {
      build.components = { ...build.components, [category]: component };
      build.totalPrice = Object.values(build.components).reduce((sum, item) => sum + item.price, 0);
    }

    newBuilds[buildIndex] = build;

    const warning = calculateBottleneck(build);

    set({
      builds: newBuilds,
      bottleneckWarning: warning,
      replaceModalOpen: false,
      replaceCategory: null,
      replacementOptions: [],
      replacementError: null,
    });
  },

  openReplaceModal: (category) => {
    const build = get().builds[get().currentBuildIndex];
    set({
      replaceModalOpen: true,
      replaceCategory: category,
      replacementOptions: [],
      replacementError: null,
    });
    if (!build.backendId || ["monitor", "keyboard", "mouse", "ups"].includes(category)) return;
    set({ replacementLoading: true });
    void (async () => {
      try {
        const token = await useAuthStore.getState().ensureAccessToken();
        const options = await api.replacementOptions(
          build,
          category as ComponentCategory,
          token,
        );
        set({ replacementOptions: options, replacementLoading: false });
      } catch (error) {
        set({
          replacementLoading: false,
          replacementError: error instanceof Error ? error.message : "Не удалось загрузить варианты",
        });
      }
    })();
  },

  closeReplaceModal: () =>
    set({
      replaceModalOpen: false,
      replaceCategory: null,
      replacementOptions: [],
      replacementError: null,
    }),

  dismissBottleneck: () => set({ bottleneckWarning: null }),

  triggerGenerate: async (prompt) => {
    const cleanPrompt = (prompt ?? get().lastPrompt).trim() || "Игровой компьютер до 6000 PLN";
    set({ isLoading: true, generationError: null, lastPrompt: cleanPrompt });
    try {
      const token = await useAuthStore.getState().ensureAccessToken();
      const generated = await api.generate(cleanPrompt, get().language, token);
      if (!generated.length) throw new ApiError(502, "Backend не вернул ни одной сборки");
      set({
        builds: generated,
        currentBuildIndex: 0,
        isLoading: false,
        showResults: true,
        bottleneckWarning: generated.length ? calculateBottleneck(generated[0]) : null,
      });
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Backend недоступен. Запустите проект через start-local-windows.bat.";
      set({ isLoading: false, generationError: message });
    }
  },

  loadSavedBuild: (build) => {
    set((state) => {
      const newBuilds = [...state.builds, build];
      return {
        builds: newBuilds,
        currentBuildIndex: newBuilds.length - 1,
        showResults: true,
        bottleneckWarning: calculateBottleneck(build),
      };
    });
  },
}));
