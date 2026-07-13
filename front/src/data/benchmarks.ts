export type BenchmarkEntry = {
  game: string;
  resolution: string;
  fps: number;
  preset: string;
};

export type WorkBenchmark = {
  task: string;
  time: string;
};

export type BenchmarkData = {
  gaming: BenchmarkEntry[];
  work: WorkBenchmark[];
};

// Benchmarks keyed by build ID
const benchmarks: Record<string, BenchmarkData> = {
  optimal: {
    gaming: [
      { game: "Cyberpunk 2077", resolution: "1440p", fps: 82, preset: "Ultra RT" },
      { game: "Counter-Strike 2", resolution: "1080p", fps: 420, preset: "High" },
      { game: "Baldur's Gate 3", resolution: "1440p", fps: 95, preset: "Ultra" },
      { game: "Elden Ring", resolution: "1440p", fps: 60, preset: "Maximum" },
      { game: "Fortnite", resolution: "1440p", fps: 165, preset: "Epic" },
    ],
    work: [
      { task: "Рендер 10 мин видео (4K, Premiere Pro)", time: "4 мин 20 сек" },
      { task: "Компиляция Unreal Engine проекта", time: "8 мин" },
      { task: "Blender BMW сцена", time: "1 мин 45 сек" },
    ],
  },
  economy: {
    gaming: [
      { game: "Cyberpunk 2077", resolution: "1080p", fps: 72, preset: "High RT" },
      { game: "Counter-Strike 2", resolution: "1080p", fps: 350, preset: "High" },
      { game: "Baldur's Gate 3", resolution: "1080p", fps: 85, preset: "Ultra" },
      { game: "Elden Ring", resolution: "1080p", fps: 60, preset: "High" },
      { game: "Fortnite", resolution: "1080p", fps: 144, preset: "Epic" },
    ],
    work: [
      { task: "Рендер 10 мин видео (4K, Premiere Pro)", time: "7 мин 10 сек" },
      { task: "Компиляция Unreal Engine проекта", time: "14 мин" },
      { task: "Blender BMW сцена", time: "3 мин 20 сек" },
    ],
  },
  futureproof: {
    gaming: [
      { game: "Cyberpunk 2077", resolution: "1440p", fps: 105, preset: "Ultra RT" },
      { game: "Counter-Strike 2", resolution: "1440p", fps: 500, preset: "High" },
      { game: "Baldur's Gate 3", resolution: "1440p", fps: 120, preset: "Ultra" },
      { game: "Elden Ring", resolution: "1440p", fps: 60, preset: "Maximum" },
      { game: "Fortnite", resolution: "4K", fps: 120, preset: "Epic" },
    ],
    work: [
      { task: "Рендер 10 мин видео (4K, Premiere Pro)", time: "2 мин 50 сек" },
      { task: "Компиляция Unreal Engine проекта", time: "5 мин" },
      { task: "Blender BMW сцена", time: "55 сек" },
    ],
  },
  amd: {
    gaming: [
      { game: "Cyberpunk 2077", resolution: "1440p", fps: 90, preset: "Ultra RT" },
      { game: "Counter-Strike 2", resolution: "1080p", fps: 550, preset: "High" },
      { game: "Baldur's Gate 3", resolution: "1440p", fps: 110, preset: "Ultra" },
      { game: "Elden Ring", resolution: "1440p", fps: 60, preset: "Maximum" },
      { game: "Fortnite", resolution: "1440p", fps: 200, preset: "Epic" },
    ],
    work: [
      { task: "Рендер 10 мин видео (4K, Premiere Pro)", time: "3 мин 40 сек" },
      { task: "Компиляция Unreal Engine проекта", time: "6 мин 30 сек" },
      { task: "Blender BMW сцена", time: "1 мин 30 сек" },
    ],
  },
  intel_nvidia: {
    gaming: [
      { game: "Cyberpunk 2077", resolution: "1440p", fps: 100, preset: "Ultra RT" },
      { game: "Counter-Strike 2", resolution: "1080p", fps: 470, preset: "High" },
      { game: "Baldur's Gate 3", resolution: "1440p", fps: 115, preset: "Ultra" },
      { game: "Elden Ring", resolution: "1440p", fps: 60, preset: "Maximum" },
      { game: "Fortnite", resolution: "4K", fps: 110, preset: "Epic" },
    ],
    work: [
      { task: "Рендер 10 мин видео (4K, Premiere Pro)", time: "3 мин" },
      { task: "Компиляция Unreal Engine проекта", time: "5 мин 45 сек" },
      { task: "Blender BMW сцена", time: "1 мин 10 сек" },
    ],
  },
};

export default benchmarks;
