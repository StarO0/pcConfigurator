export type ShopLink = {
  shop: string;
  url: string;
  price: number;
};

export type Component = {
  id: string;
  category: ComponentCategory;
  name: string;
  price: number;
  shopLinks: ShopLink[];
  specs: Record<string, string>;
  tier?: "budget" | "mid" | "high" | "enthusiast";
  image?: string;
  /** Estimated power draw in Watts (TDP for CPU/GPU, system draw for other parts) */
  wattage?: number;
};

export type ComponentCategory =
  | "cpu"
  | "gpu"
  | "ram"
  | "ssd"
  | "motherboard"
  | "psu"
  | "case"
  | "cooler";

export type PeripheralCategory = "monitor" | "keyboard" | "mouse" | "ups";
export type AllCategory = ComponentCategory | PeripheralCategory;

export type Build = {
  id: string;
  category: BuildCategory;
  components: Record<ComponentCategory, Component> & Partial<Record<PeripheralCategory, Component>>;
  totalPrice: number;
  aiExplanation: Record<string, string>;
  badge: { label: Record<string, string>; color: string };
  /** Per-component AI reasoning why each part was chosen (localized) */
  componentReasons?: Partial<Record<AllCategory, Record<string, string>>>;
};

export type BuildCategory =
  | "optimal"
  | "economy"
  | "futureproof"
  | "amd"
  | "intel_nvidia";

export const COMPONENT_LABELS: Record<AllCategory, Record<string, string>> = {
  cpu: { en: "Processor", ru: "Процессор", uk: "Процесор", pl: "Procesor" },
  gpu: { en: "Graphics Card", ru: "Видеокарта", uk: "Відеокарта", pl: "Karta graficzna" },
  ram: { en: "RAM", ru: "Оперативная память", uk: "Оперативна пам'ять", pl: "Pamięć RAM" },
  ssd: { en: "Storage", ru: "Накопитель", uk: "Накопичувач", pl: "Dysk" },
  motherboard: { en: "Motherboard", ru: "Материнская плата", uk: "Материнська плата", pl: "Płyta główna" },
  psu: { en: "Power Supply", ru: "Блок питания", uk: "Блок живлення", pl: "Zasilacz" },
  case: { en: "Case", ru: "Корпус", uk: "Корпус", pl: "Obudowa" },
  cooler: { en: "Cooler", ru: "Кулер", uk: "Кулер", pl: "Chłodzenie" },
  monitor: { en: "Monitor", ru: "Монитор", uk: "Монітор", pl: "Monitor" },
  keyboard: { en: "Keyboard", ru: "Клавиатура", uk: "Клавіатура", pl: "Klawiatura" },
  mouse: { en: "Mouse", ru: "Мышь", uk: "Миша", pl: "Mysz" },
  ups: { en: "UPS", ru: "ИБП", uk: "ДБЖ", pl: "Zasilacz awaryjny (UPS)" },
};

export const CATEGORY_ORDER: AllCategory[] = [
  "cpu", "gpu", "ram", "ssd", "motherboard", "psu", "case", "cooler",
  "monitor", "keyboard", "mouse", "ups"
];

const builds: Build[] = [
  // 1. Оптимальный выбор
  {
    id: "optimal",
    category: "optimal",
    badge: {
      label: { en: "Optimal Choice", ru: "Оптимальный выбор", uk: "Оптимальний вибір", pl: "Optymalny wybór" },
      color: "#22c55e",
    },
    totalPrice: 5849,
    aiExplanation: {
      en: "This build perfectly balances performance and price. The Ryzen 7 9700X pairs excellently with the RTX 5070 — no bottlenecks, pure power for 1440p gaming and content creation. The 32GB DDR5 RAM is the sweet spot for modern games, and the 1TB Gen4 NVMe ensures instant load times. The Deepcool AK400 keeps the CPU cool and quiet without overpaying for liquid cooling.",
      ru: "Эта сборка идеально балансирует производительность и цену. Ryzen 7 9700X отлично сочетается с RTX 5070 — никаких боттлнеков, чистая мощь для 1440p гейминга и создания контента. 32 ГБ DDR5 RAM — золотая середина для современных игр, а 1 ТБ Gen4 NVMe обеспечивает мгновенную загрузку. Deepcool AK400 охлаждает процессор тихо и эффективно, без переплаты за водянку.",
      uk: "Ця збірка ідеально балансує продуктивність та ціну. Ryzen 7 9700X чудово поєднується з RTX 5070 — жодних боттлнеків, чиста потужність для 1440p гейінгу та створення контенту. 32 ГБ DDR5 RAM — золота середина для сучасних ігор, а 1 ТБ Gen4 NVMe забезпечує миттєве завантаження.",
      pl: "Ten zestaw idealnie równoważy wydajność i cenę. Ryzen 7 9700X doskonale współpracuje z RTX 5070 — bez bottlenecków, czysta moc do grania w 1440p i tworzenia treści. 32 GB DDR5 RAM to złoty środek dla nowoczesnych gier, a 1 TB Gen4 NVMe zapewnia natychmiastowe ładowanie.",
    },
    componentReasons: {
      cpu: { en: "8-core Zen 5 perfectly handles 1440p gaming without bottlenecking the RTX 5070. Lower TDP means less heat and noise.", ru: "8-ядерный Zen 5 идеально справляется с 1440p без боттлнека RTX 5070. Низкий TDP — меньше тепла и шума.", uk: "8-ядерний Zen 5 ідеально справляється з 1440p без боттлнека RTX 5070.", pl: "8-rdzeniowy Zen 5 bez bottlenecku obsługuje 1440p z RTX 5070. Niski TDP = mniej ciepła." },
      gpu: { en: "RTX 5070 delivers 60-100+ FPS in all modern AAA games at 1440p Ultra settings. DLSS 4 extends performance further.", ru: "RTX 5070 выдаёт 60-100+ FPS в любой современной AAA-игре на Ultra 1440p. DLSS 4 усиливает производительность.", uk: "RTX 5070 видає 60-100+ FPS у будь-якій сучасній AAA-грі на Ultra 1440p.", pl: "RTX 5070 zapewnia 60-100+ FPS w każdej grze AAA przy 1440p Ultra. DLSS 4 zwiększa wydajność." },
      ram: { en: "32GB DDR5-6000 CL30 hits the sweet spot for AM5 — fast enough for gaming, plenty for streaming and content creation.", ru: "32 ГБ DDR5-6000 CL30 — золотая середина для AM5. Достаточно быстро для игр и потокового монтажа.", uk: "32 ГБ DDR5-6000 CL30 — золота середина для AM5.", pl: "32 GB DDR5-6000 CL30 to złoty środek dla AM5 — wystarczająco szybko do grania i streamingu." },
      ssd: { en: "Gen4 NVMe with 5150 MB/s read speed eliminates load screens. WD Black is reliable with a 5-year warranty.", ru: "NVMe Gen4 со скоростью 5150 МБ/с устраняет экраны загрузки. WD Black надёжен и имеет 5-летнюю гарантию.", uk: "NVMe Gen4 зі швидкістю 5150 МБ/с усуває екрани завантаження.", pl: "Gen4 NVMe z 5150 MB/s eliminuje ekrany ładowania. WD Black ma gwarancję 5 lat." },
      motherboard: { en: "B650 chipset with PCIe 5.0 lanes and WiFi 6E gives full AM5 feature set without overpaying for X670.", ru: "Чипсет B650 с PCIe 5.0 и WiFi 6E даёт всё необходимое от AM5 без переплаты за X670.", uk: "Чіпсет B650 з PCIe 5.0 та WiFi 6E дає повний функціонал AM5.", pl: "Chipset B650 z PCIe 5.0 i WiFi 6E daje pełen zestaw funkcji AM5 bez przepłacania za X670." },
      psu: { en: "750W Gold-rated PSU gives 100W headroom above peak draw, ensuring stable power delivery and room to upgrade.", ru: "Блок питания 750W Gold с запасом 100W выше пиковой нагрузки обеспечивает стабильное питание и запас для апгрейда.", uk: "БЖ 750W Gold із запасом 100W забезпечує стабільне живлення та можливість апгрейду.", pl: "Zasilacz 750W Gold z 100W zapasem powyżej szczytowego poboru zapewnia stabilne zasilanie i miejsce na upgrade." },
      case: { en: "4000D Airflow is engineered for maximum airflow with mesh front panel. Two pre-installed 120mm fans keep everything cool.", ru: "4000D Airflow создан для максимального воздушного потока с сетчатой передней панелью. Два вентилятора 120 мм в комплекте.", uk: "4000D Airflow спроектований для максимального повітряного потоку.", pl: "4000D Airflow ma siatkowy panel przedni dla maksymalnego przepływu powietrza. Dwa wentylatory 120mm w zestawie." },
      cooler: { en: "AK400 Digital handles 65W TDP with a comfortable margin. The digital display is a nice bonus without breaking the budget.", ru: "AK400 Digital справляется с 65W TDP с хорошим запасом. Цифровой дисплей — приятный бонус без переплаты.", uk: "AK400 Digital справляється з 65W TDP з хорошим запасом.", pl: "AK400 Digital obsługuje 65W TDP z zapasem. Wyświetlacz cyfrowy to miły bonus bez przekraczania budżetu." },
    },
    components: {
      cpu: {
        id: "cpu-r7-9700x",
        category: "cpu",
        name: "AMD Ryzen 7 9700X",
        price: 1399,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1399 },
          { shop: "Morele", url: "https://morele.net", price: 1429 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 1449 },
        ],
        specs: { cores: "8C/16T", boost: "5.5 GHz", tdp: "65W", socket: "AM5" },
        wattage: 65,
      },
      gpu: {
        id: "gpu-rtx5070",
        category: "gpu",
        name: "MSI GeForce RTX 5070 Ventus 3X OC",
        price: 2899,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 2899 },
          { shop: "Morele", url: "https://morele.net", price: 2949 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 2979 },
        ],
        specs: { vram: "12 GB GDDR7", boost: "2512 MHz", tdp: "250W", length: "307mm" },
        wattage: 250,
      },
      ram: {
        id: "ram-32gb-ddr5-6000",
        category: "ram",
        name: "G.Skill Trident Z5 Neo 32GB DDR5 6000MHz CL30",
        price: 479,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 479 },
          { shop: "Morele", url: "https://morele.net", price: 499 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 489 },
        ],
        specs: { capacity: "2x16 GB", speed: "6000 MHz", latency: "CL30", type: "DDR5" },
        wattage: 5,
      },
      ssd: {
        id: "ssd-wd-sn770-1tb",
        category: "ssd",
        name: "WD Black SN770 1TB NVMe Gen4",
        price: 289,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 289 },
          { shop: "Morele", url: "https://morele.net", price: 299 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 295 },
        ],
        specs: { capacity: "1 TB", read: "5150 MB/s", write: "4900 MB/s", interface: "PCIe 4.0" },
        wattage: 8,
      },
      motherboard: {
        id: "mb-b650-tomahawk",
        category: "motherboard",
        name: "MSI MAG B650 TOMAHAWK WiFi",
        price: 799,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 799 },
          { shop: "Morele", url: "https://morele.net", price: 819 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 829 },
        ],
        specs: { socket: "AM5", chipset: "B650", ram: "DDR5", formFactor: "ATX" },
        wattage: 30,
      },
      psu: {
        id: "psu-rm750e",
        category: "psu",
        name: "Corsair RM750e 750W 80+ Gold",
        price: 429,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 429 },
          { shop: "Morele", url: "https://morele.net", price: 449 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 439 },
        ],
        specs: { wattage: "750W", efficiency: "80+ Gold", modular: "Full", fan: "120mm" },
        wattage: 0,
      },
      case: {
        id: "case-4000d-airflow",
        category: "case",
        name: "Corsair 4000D Airflow",
        price: 389,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 389 },
          { shop: "Morele", url: "https://morele.net", price: 399 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 395 },
        ],
        specs: { formFactor: "Mid Tower", maxGpu: "360mm", maxCooler: "170mm", fans: "2x 120mm" },
        wattage: 0,
      },
      cooler: {
        id: "cooler-ak400",
        category: "cooler",
        name: "Deepcool AK400 Digital",
        price: 199,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 199 },
          { shop: "Morele", url: "https://morele.net", price: 209 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 205 },
        ],
        specs: { type: "Tower", height: "155mm", tdp: "220W", fan: "120mm" },
        wattage: 5,
      },
    },
  },

  // 2. Максимальная экономия (Cebula-build)
  {
    id: "economy",
    category: "economy",
    badge: {
      label: { en: "Maximum Savings", ru: "Максимальная экономия", uk: "Максимальна економія", pl: "Maksymalna oszczędność" },
      color: "#eab308",
    },
    totalPrice: 3579,
    aiExplanation: {
      en: "The Cebula-build! Maximum value for every złoty. The Ryzen 5 7500F is a hidden gem — almost identical gaming performance to its bigger brothers at half the price. The RX 7700 XT gives RTX 4070-level performance for significantly less. We picked B650 motherboard to keep the AM5 upgrade path open.",
      ru: "Cebula-build! Максимум отдачи за каждый злотый. Ryzen 5 7500F — скрытый бриллиант: почти идентичная игровая производительность с братьями побольше за половину цены. RX 7700 XT даёт производительность на уровне RTX 4070 за значительно меньшие деньги. Выбрали B650 плату, чтобы сохранить путь апгрейда AM5.",
      uk: "Cebula-build! Максимум віддачі за кожен злотий. Ryzen 5 7500F — прихований діамант: майже ідентична ігрова продуктивність з більшими братами за половину ціни. RX 7700 XT дає продуктивність на рівні RTX 4070 за значно менші гроші.",
      pl: "Cebula-build! Maksimum wydajności za każdą złotówkę. Ryzen 5 7500F to ukryty diament — niemal identyczna wydajność w grach jak starsi bracia za połowę ceny. RX 7700 XT daje wydajność na poziomie RTX 4070 za znacznie mniej.",
    },
    componentReasons: {
      cpu: { en: "Ryzen 5 7500F is CPU-only (no iGPU) so costs less, perfect pairing for a dedicated GPU budget build.", ru: "Ryzen 5 7500F без встроенной графики стоит дешевле — идеально для бюджетной сборки с дискретной видеокартой.", uk: "Ryzen 5 7500F без інтегрованої графіки коштує менше.", pl: "Ryzen 5 7500F bez iGPU jest tańszy — idealne do budżetowego zestawu z dedykowaną kartą." },
      gpu: { en: "RX 7700 XT delivers 1080p Ultra and 1440p Medium at minimal cost. Best price-per-frame in this budget range.", ru: "RX 7700 XT обеспечивает Ultra 1080p и Medium 1440p за минимальные деньги. Лучшая цена за кадр в бюджетном диапазоне.", uk: "RX 7700 XT забезпечує Ultra 1080p та Medium 1440p за мінімальну ціну.", pl: "RX 7700 XT zapewnia Ultra 1080p i Medium 1440p za minimalny koszt. Najlepszy stosunek ceny do FPS." },
    },
    components: {
      cpu: {
        id: "cpu-r5-7500f",
        category: "cpu",
        name: "AMD Ryzen 5 7500F",
        price: 549,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 549 },
          { shop: "Morele", url: "https://morele.net", price: 559 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 569 },
        ],
        specs: { cores: "6C/12T", boost: "5.0 GHz", tdp: "65W", socket: "AM5" },
        wattage: 65,
      },
      gpu: {
        id: "gpu-rx7700xt",
        category: "gpu",
        name: "Sapphire Pulse RX 7700 XT 12GB",
        price: 1899,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1899 },
          { shop: "Morele", url: "https://morele.net", price: 1929 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 1949 },
        ],
        specs: { vram: "12 GB GDDR6", boost: "2584 MHz", tdp: "245W", length: "267mm" },
        wattage: 115,
      },
      ram: {
        id: "ram-16gb-ddr5-5600",
        category: "ram",
        name: "Kingston Fury Beast 16GB DDR5 5600MHz",
        price: 219,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 219 },
          { shop: "Morele", url: "https://morele.net", price: 229 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 225 },
        ],
        specs: { capacity: "2x8 GB", speed: "5600 MHz", latency: "CL36", type: "DDR5" },
        wattage: 5,
      },
      ssd: {
        id: "ssd-lexar-nm710-1tb",
        category: "ssd",
        name: "Lexar NM710 1TB NVMe Gen4",
        price: 219,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 219 },
          { shop: "Morele", url: "https://morele.net", price: 229 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 225 },
        ],
        specs: { capacity: "1 TB", read: "5000 MB/s", write: "4500 MB/s", interface: "PCIe 4.0" },
        wattage: 5,
      },
      motherboard: {
        id: "mb-b650m-k",
        category: "motherboard",
        name: "ASUS PRIME B650M-K",
        price: 449,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 449 },
          { shop: "Morele", url: "https://morele.net", price: 459 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 469 },
        ],
        specs: { socket: "AM5", chipset: "B650", ram: "DDR5", formFactor: "mATX" },
        wattage: 25,
      },
      psu: {
        id: "psu-cv550",
        category: "psu",
        name: "Corsair CV550 550W 80+ Bronze",
        price: 219,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 219 },
          { shop: "Morele", url: "https://morele.net", price: 229 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 225 },
        ],
        specs: { wattage: "550W", efficiency: "80+ Bronze", modular: "No", fan: "120mm" },
        wattage: 0,
      },
      case: {
        id: "case-masterbox-q300l",
        category: "case",
        name: "Cooler Master MasterBox Q300L v2",
        price: 189,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 189 },
          { shop: "Morele", url: "https://morele.net", price: 199 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 195 },
        ],
        specs: { formFactor: "Mini Tower", maxGpu: "360mm", maxCooler: "159mm", fans: "1x 120mm" },
        wattage: 0,
      },
      cooler: {
        id: "cooler-hyper212",
        category: "cooler",
        name: "Cooler Master Hyper 212 Spectrum V3",
        price: 129,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 129 },
          { shop: "Morele", url: "https://morele.net", price: 139 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 135 },
        ],
        specs: { type: "Tower", height: "158mm", tdp: "150W", fan: "120mm" },
        wattage: 5,
      },
    },
  },

  // 3. На вырост
  {
    id: "futureproof",
    category: "futureproof",
    badge: {
      label: { en: "Future-Proof", ru: "На вырост", uk: "На виріст", pl: "Na przyszłość" },
      color: "#3b82f6",
    },
    totalPrice: 8299,
    aiExplanation: {
      en: "Built for tomorrow. The X870 board supports everything AM5 will offer for years. The 1000W PSU has headroom for any future GPU upgrade. DDR5-6400 ensures you're set for next-gen games. The Torrent case has best-in-class airflow that will handle any hardware you throw at it.",
      ru: "Собрана на завтра. Плата X870 поддерживает всё, что AM5 предложит на годы вперёд. БП на 1000W имеет запас для любого будущего GPU. DDR5-6400 гарантирует готовность к играм следующего поколения. Корпус Torrent имеет лучший в классе поток воздуха.",
      uk: "Зібрана на завтра. Плата X870 підтримує все, що AM5 запропонує на роки вперед. БЖ на 1000W має запас для будь-якого майбутнього GPU. DDR5-6400 гарантує готовність до ігор наступного покоління.",
      pl: "Zbudowany na jutro. Płyta X870 obsługuje wszystko, co AM5 zaoferuje na lata. Zasilacz 1000W ma zapas na każdy przyszły GPU. DDR5-6400 zapewnia gotowość na gry nowej generacji.",
    },
    componentReasons: {
      cpu: { en: "Ryzen 9 9900X's 12 cores are overkill for gaming today but essential for 4K video editing, 3D rendering, and AI tasks.", ru: "12 ядер Ryzen 9 9900X — избыточны для игр, но незаменимы для монтажа 4K, 3D-рендеринга и ИИ-задач.", uk: "12 ядер Ryzen 9 9900X незамінні для монтажу 4K та 3D-рендерингу.", pl: "12 rdzeni Ryzen 9 9900X to nadmiar dla gier, ale niezbędne do edycji 4K i renderingu 3D." },
      gpu: { en: "RTX 5070 Ti with 16GB VRAM handles 4K gaming and AI workloads. The extra VRAM future-proofs against upcoming game demands.", ru: "RTX 5070 Ti с 16 ГБ VRAM справляется с 4K играми и ИИ-задачами. Запас VRAM защищает от будущих требований.", uk: "RTX 5070 Ti з 16 ГБ VRAM впорається з 4K іграми та ІІ-задачами.", pl: "RTX 5070 Ti z 16 GB VRAM obsługuje gry 4K i obciążenia AI. Extra VRAM zabezpiecza na przyszłość." },
    },
    components: {
      cpu: {
        id: "cpu-r9-9900x",
        category: "cpu",
        name: "AMD Ryzen 9 9900X",
        price: 2199,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 2199 },
          { shop: "Morele", url: "https://morele.net", price: 2249 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 2279 },
        ],
        specs: { cores: "12C/24T", boost: "5.6 GHz", tdp: "120W", socket: "AM5" },
        wattage: 170,
      },
      gpu: {
        id: "gpu-rtx5070ti",
        category: "gpu",
        name: "ASUS TUF Gaming RTX 5070 Ti OC",
        price: 3999,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 3999 },
          { shop: "Morele", url: "https://morele.net", price: 4049 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 4079 },
        ],
        specs: { vram: "16 GB GDDR7", boost: "2452 MHz", tdp: "300W", length: "321mm" },
        wattage: 300,
      },
      ram: {
        id: "ram-32gb-ddr5-6400",
        category: "ram",
        name: "Corsair Dominator Titanium 32GB DDR5 6400MHz CL28",
        price: 699,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 699 },
          { shop: "Morele", url: "https://morele.net", price: 719 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 729 },
        ],
        specs: { capacity: "2x16 GB", speed: "6400 MHz", latency: "CL28", type: "DDR5" },
        wattage: 5,
      },
      ssd: {
        id: "ssd-990-pro-2tb",
        category: "ssd",
        name: "Samsung 990 Pro 2TB NVMe Gen4",
        price: 699,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 699 },
          { shop: "Morele", url: "https://morele.net", price: 719 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 729 },
        ],
        specs: { capacity: "2 TB", read: "7450 MB/s", write: "6900 MB/s", interface: "PCIe 4.0" },
        wattage: 8,
      },
      motherboard: {
        id: "mb-x870-ace",
        category: "motherboard",
        name: "MSI MEG X870 ACE WiFi",
        price: 1899,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1899 },
          { shop: "Morele", url: "https://morele.net", price: 1929 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 1949 },
        ],
        specs: { socket: "AM5", chipset: "X870", ram: "DDR5", formFactor: "E-ATX" },
        wattage: 40,
      },
      psu: {
        id: "psu-hx1000",
        category: "psu",
        name: "Corsair HX1000 1000W 80+ Platinum",
        price: 849,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 849 },
          { shop: "Morele", url: "https://morele.net", price: 869 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 879 },
        ],
        specs: { wattage: "1000W", efficiency: "80+ Platinum", modular: "Full", fan: "135mm" },
        wattage: 0,
      },
      case: {
        id: "case-torrent",
        category: "case",
        name: "Fractal Design Torrent",
        price: 699,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 699 },
          { shop: "Morele", url: "https://morele.net", price: 719 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 729 },
        ],
        specs: { formFactor: "Full Tower", maxGpu: "461mm", maxCooler: "188mm", fans: "2x 180mm + 3x 140mm" },
        wattage: 0,
      },
      cooler: {
        id: "cooler-le-grand-macho",
        category: "cooler",
        name: "Thermalright Le Grand Macho RT",
        price: 299,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 299 },
          { shop: "Morele", url: "https://morele.net", price: 309 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 315 },
        ],
        specs: { type: "Tower", height: "159mm", tdp: "250W", fan: "140mm" },
        wattage: 8,
      },
    },
  },

  // 4. Сборка AMD
  {
    id: "amd",
    category: "amd",
    badge: {
      label: { en: "Team Red (AMD)", ru: "Сборка AMD", uk: "Збірка AMD", pl: "Drużyna AMD" },
      color: "#ef4444",
    },
    totalPrice: 6199,
    aiExplanation: {
      en: "All-AMD ecosystem. The Ryzen 7 9800X3D is the undisputed king of gaming thanks to 3D V-Cache. Paired with the RX 9070 XT, you get a pure AMD setup with excellent driver-level optimizations. Smart Access Memory (SAM) gives a free performance boost between AMD CPU and GPU.",
      ru: "Полная экосистема AMD. Ryzen 7 9800X3D — бесспорный король гейминга благодаря 3D V-Cache. В паре с RX 9070 XT вы получаете чисто AMD-связку с отличными оптимизациями на уровне драйверов. Smart Access Memory (SAM) даёт бесплатный прирост производительности.",
      uk: "Повна екосистема AMD. Ryzen 7 9800X3D — безсумнівний король гейінгу завдяки 3D V-Cache. У парі з RX 9070 XT ви отримуєте чисто AMD-зв'язку з відмінними оптимізаціями на рівні драйверів.",
      pl: "Pełny ekosystem AMD. Ryzen 7 9800X3D to niekwestionowany król gamingu dzięki 3D V-Cache. W parze z RX 9070 XT dostajesz czysty setup AMD z doskonałą optymalizacją na poziomie sterowników.",
    },
    componentReasons: {
      cpu: { en: "Ryzen 7 9700X is the best AMD mid-range CPU — 8 cores, Zen 5 IPC improvements, and excellent single-thread performance.", ru: "Ryzen 7 9700X — лучший AMD процессор среднего класса: 8 ядер, IPC Zen 5 и отличная однопоточная производительность.", uk: "Ryzen 7 9700X — найкращий AMD процесор середнього класу.", pl: "Ryzen 7 9700X to najlepszy AMD mid-range — 8 rdzeni, Zen 5 IPC i doskonała wydajność jednowątkowa." },
      gpu: { en: "RX 9070 XT is AMD's answer to RTX 5070 — matching rasterization performance at a better price with 16GB GDDR6.", ru: "RX 9070 XT — ответ AMD на RTX 5070: сопоставимая растеризация по лучшей цене с 16 ГБ GDDR6.", uk: "RX 9070 XT — відповідь AMD на RTX 5070 з кращою ціною та 16 ГБ GDDR6.", pl: "RX 9070 XT to odpowiedź AMD na RTX 5070 — porównywalna wydajność w lepszej cenie z 16 GB GDDR6." },
    },
    components: {
      cpu: {
        id: "cpu-r7-9800x3d",
        category: "cpu",
        name: "AMD Ryzen 7 9800X3D",
        price: 1999,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1999 },
          { shop: "Morele", url: "https://morele.net", price: 2029 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 2049 },
        ],
        specs: { cores: "8C/16T", boost: "5.2 GHz", tdp: "120W", socket: "AM5" },
        wattage: 65,
      },
      gpu: {
        id: "gpu-rx9070xt",
        category: "gpu",
        name: "XFX Speedster MERC310 RX 9070 XT 16GB",
        price: 2799,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 2799 },
          { shop: "Morele", url: "https://morele.net", price: 2849 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 2879 },
        ],
        specs: { vram: "16 GB GDDR6", boost: "2950 MHz", tdp: "300W", length: "322mm" },
        wattage: 220,
      },
      ram: {
        id: "ram-32gb-ddr5-6000-amd",
        category: "ram",
        name: "G.Skill Trident Z5 Neo RGB 32GB DDR5 6000MHz CL30",
        price: 529,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 529 },
          { shop: "Morele", url: "https://morele.net", price: 549 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 539 },
        ],
        specs: { capacity: "2x16 GB", speed: "6000 MHz", latency: "CL30", type: "DDR5" },
        wattage: 5,
      },
      ssd: {
        id: "ssd-wd-sn850x-1tb",
        category: "ssd",
        name: "WD Black SN850X 1TB NVMe Gen4",
        price: 349,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 349 },
          { shop: "Morele", url: "https://morele.net", price: 359 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 365 },
        ],
        specs: { capacity: "1 TB", read: "7300 MB/s", write: "6300 MB/s", interface: "PCIe 4.0" },
        wattage: 8,
      },
      motherboard: {
        id: "mb-b650-aorus-elite",
        category: "motherboard",
        name: "Gigabyte B650 AORUS ELITE AX V2",
        price: 749,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 749 },
          { shop: "Morele", url: "https://morele.net", price: 769 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 779 },
        ],
        specs: { socket: "AM5", chipset: "B650", ram: "DDR5", formFactor: "ATX" },
        wattage: 30,
      },
      psu: {
        id: "psu-rm850x",
        category: "psu",
        name: "Corsair RM850x 850W 80+ Gold",
        price: 549,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 549 },
          { shop: "Morele", url: "https://morele.net", price: 569 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 559 },
        ],
        specs: { wattage: "850W", efficiency: "80+ Gold", modular: "Full", fan: "135mm" },
        wattage: 0,
      },
      case: {
        id: "case-lancool-iii",
        category: "case",
        name: "Lian Li Lancool III",
        price: 549,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 549 },
          { shop: "Morele", url: "https://morele.net", price: 569 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 559 },
        ],
        specs: { formFactor: "Mid Tower", maxGpu: "420mm", maxCooler: "187mm", fans: "3x 140mm" },
        wattage: 0,
      },
      cooler: {
        id: "cooler-ak620",
        category: "cooler",
        name: "Deepcool AK620 Digital",
        price: 279,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 279 },
          { shop: "Morele", url: "https://morele.net", price: 289 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 285 },
        ],
        specs: { type: "Dual Tower", height: "160mm", tdp: "260W", fan: "2x 120mm" },
        wattage: 5,
      },
    },
  },

  // 5. Сборка Intel + NVIDIA
  {
    id: "intel_nvidia",
    category: "intel_nvidia",
    badge: {
      label: { en: "Team Blue+Green", ru: "Intel + NVIDIA", uk: "Intel + NVIDIA", pl: "Intel + NVIDIA" },
      color: "#06b6d4",
    },
    totalPrice: 6399,
    aiExplanation: {
      en: "The classic Intel + NVIDIA combo. The Core Ultra 7 265K brings the latest hybrid architecture with E-cores and P-cores for multitasking. The RTX 5070 Ti gives you DLSS 4 and ray tracing — technologies exclusive to NVIDIA. Perfect for creators who also game.",
      ru: "Классическая связка Intel + NVIDIA. Core Ultra 7 265K приносит новейшую гибридную архитектуру с E- и P-ядрами для многозадачности. RTX 5070 Ti даёт DLSS 4 и рейтрейсинг — эксклюзивные технологии NVIDIA. Идеально для креаторов, которые также играют.",
      uk: "Класична зв'язка Intel + NVIDIA. Core Ultra 7 265K приносить новітню гібридну архітектуру з E- та P-ядрами для багатозадачності. RTX 5070 Ti дає DLSS 4 та рейтрейсинг — ексклюзивні технології NVIDIA.",
      pl: "Klasyczne połączenie Intel + NVIDIA. Core Ultra 7 265K oferuje najnowszą hybrydową architekturę z rdzeniami E i P do wielozadaniowości. RTX 5070 Ti daje DLSS 4 i ray tracing — technologie ekskluzywne dla NVIDIA.",
    },
    componentReasons: {
      cpu: { en: "Core Ultra 7 265K offers Intel's top single-thread IPC for gaming plus strong multi-thread for content creation.", ru: "Core Ultra 7 265K предлагает лучший IPC Intel для гейминга и сильную многопоточность для создания контента.", uk: "Core Ultra 7 265K пропонує найкращий IPC Intel для гейінгу.", pl: "Core Ultra 7 265K oferuje najlepszy IPC Intela do grania i wydajność wielowątkową do tworzenia treści." },
      gpu: { en: "RTX 5070 Ti paired with Intel maximizes DLSS 4 and multi-frame generation, especially effective at 4K with DLSS Quality.", ru: "RTX 5070 Ti с Intel максимизирует DLSS 4 и мультикадровую генерацию — особенно эффективно при 4K с DLSS Quality.", uk: "RTX 5070 Ti з Intel максимізує DLSS 4 та мультикадрову генерацію.", pl: "RTX 5070 Ti z Intelem maksymalizuje DLSS 4 i multi-frame generation, szczególnie w 4K z DLSS Quality." },
    },
    components: {
      cpu: {
        id: "cpu-i7-265k",
        category: "cpu",
        name: "Intel Core Ultra 7 265K",
        price: 1699,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1699 },
          { shop: "Morele", url: "https://morele.net", price: 1729 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 1749 },
        ],
        specs: { cores: "8P+12E/28T", boost: "5.5 GHz", tdp: "125W", socket: "LGA1851" },
        wattage: 125,
      },
      gpu: {
        id: "gpu-rtx5070ti-intel",
        category: "gpu",
        name: "Gigabyte GeForce RTX 5070 Ti Gaming OC",
        price: 3899,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 3899 },
          { shop: "Morele", url: "https://morele.net", price: 3949 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 3979 },
        ],
        specs: { vram: "16 GB GDDR7", boost: "2452 MHz", tdp: "300W", length: "329mm" },
        wattage: 300,
      },
      ram: {
        id: "ram-32gb-ddr5-6400-intel",
        category: "ram",
        name: "Kingston Fury Renegade 32GB DDR5 6400MHz CL32",
        price: 579,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 579 },
          { shop: "Morele", url: "https://morele.net", price: 599 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 589 },
        ],
        specs: { capacity: "2x16 GB", speed: "6400 MHz", latency: "CL32", type: "DDR5" },
        wattage: 5,
      },
      ssd: {
        id: "ssd-990-evo-2tb",
        category: "ssd",
        name: "Samsung 990 EVO Plus 2TB NVMe Gen5",
        price: 599,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 599 },
          { shop: "Morele", url: "https://morele.net", price: 619 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 609 },
        ],
        specs: { capacity: "2 TB", read: "10000 MB/s", write: "8000 MB/s", interface: "PCIe 5.0" },
        wattage: 8,
      },
      motherboard: {
        id: "mb-z890-tomahawk",
        category: "motherboard",
        name: "MSI MAG Z890 TOMAHAWK WiFi",
        price: 1199,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1199 },
          { shop: "Morele", url: "https://morele.net", price: 1229 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 1249 },
        ],
        specs: { socket: "LGA1851", chipset: "Z890", ram: "DDR5", formFactor: "ATX" },
        wattage: 40,
      },
      psu: {
        id: "psu-rm850x-intel",
        category: "psu",
        name: "Corsair RM850x 850W 80+ Gold",
        price: 549,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 549 },
          { shop: "Morele", url: "https://morele.net", price: 569 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 559 },
        ],
        specs: { wattage: "850W", efficiency: "80+ Gold", modular: "Full", fan: "135mm" },
        wattage: 0,
      },
      case: {
        id: "case-h7-flow",
        category: "case",
        name: "NZXT H7 Flow",
        price: 499,
        tier: "high",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 499 },
          { shop: "Morele", url: "https://morele.net", price: 519 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 509 },
        ],
        specs: { formFactor: "Mid Tower", maxGpu: "400mm", maxCooler: "185mm", fans: "2x 120mm" },
        wattage: 0,
      },
      cooler: {
        id: "cooler-assassin-iv",
        category: "cooler",
        name: "Deepcool Assassin IV",
        price: 349,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 349 },
          { shop: "Morele", url: "https://morele.net", price: 359 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 365 },
        ],
        specs: { type: "Dual Tower", height: "164mm", tdp: "280W", fan: "1x 120mm + 1x 140mm" },
        wattage: 8,
      },
    },
  },
];

export default builds;
