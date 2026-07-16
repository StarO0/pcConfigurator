export type Peripheral = {
  id: string;
  name: string;
  category: string;
  price: number;
  description: Record<string, string>;
  shopUrl: string;
  tag: Record<string, string>;
};

const peripherals: Peripheral[] = [
  {
    id: "monitor-1",
    name: "LG 27GP850-B 27\" 1440p 165Hz Nano IPS",
    category: "monitor",
    price: 1299,
    description: {
      en: "Unlock the full potential of your GPU with a 1440p 165Hz display. Nano IPS for vivid, accurate colors.",
      ru: "Раскройте весь потенциал вашей видеокарты с дисплеем 1440p 165Hz. Nano IPS для ярких и точных цветов.",
      uk: "Розкрийте весь потенціал вашої відеокарти з дисплеєм 1440p 165Hz.",
      pl: "Odblokuj pełny potencjał GPU z wyświetlaczem 1440p 165Hz. Nano IPS dla żywych kolorów.",
    },
    shopUrl: "https://x-kom.pl",
    tag: { en: "Best for Gaming", ru: "Лучший для гейминга", uk: "Найкращий для гейінгу", pl: "Najlepszy do grania" },
  },
  {
    id: "monitor-2",
    name: "Samsung Odyssey G7 32\" 4K 240Hz",
    category: "monitor",
    price: 2499,
    description: {
      en: "The ultimate gaming monitor. 4K at 240Hz with HDR600 — for builds that can handle it.",
      ru: "Абсолютный игровой монитор. 4K на 240Hz с HDR600 — для сборок, которые могут это потянуть.",
      uk: "Абсолютний ігровий монітор. 4K на 240Hz з HDR600.",
      pl: "Najlepszy monitor gamingowy. 4K przy 240Hz z HDR600.",
    },
    shopUrl: "https://x-kom.pl",
    tag: { en: "Premium Pick", ru: "Премиум выбор", uk: "Преміум вибір", pl: "Wybór premium" },
  },
  {
    id: "keyboard-1",
    name: "Keychron Q1 Max 75% Mechanical",
    category: "keyboard",
    price: 799,
    description: {
      en: "Premium wireless mechanical keyboard with hot-swappable switches. Aluminium CNC body.",
      ru: "Премиальная беспроводная механическая клавиатура с hot-swap переключателями. Корпус из алюминия CNC.",
      uk: "Преміальна бездротова механічна клавіатура з hot-swap перемикачами.",
      pl: "Premiumowa bezprzewodowa klawiatura mechaniczna z przełącznikami hot-swap.",
    },
    shopUrl: "https://x-kom.pl",
    tag: { en: "Best Keyboard", ru: "Лучшая клавиатура", uk: "Найкраща клавіатура", pl: "Najlepsza klawiatura" },
  },
  {
    id: "ups-1",
    name: "APC Back-UPS Pro 1500VA",
    category: "ups",
    price: 1099,
    description: {
      en: "Protect your investment. Power outage won't destroy your hardware or corrupt your saves.",
      ru: "Защитите свою инвестицию. Перебои питания не уничтожат ваше оборудование и не повредят сохранения.",
      uk: "Захистіть свою інвестицію. Перебої живлення не знищать ваше обладнання.",
      pl: "Chroń swoją inwestycję. Przerwy w zasilaniu nie zniszczą sprzętu ani zapisów.",
    },
    shopUrl: "https://x-kom.pl",
    tag: { en: "Safety First", ru: "Защита питания", uk: "Захист живлення", pl: "Bezpieczeństwo" },
  },
  {
    id: "mouse-1",
    name: "Logitech G Pro X Superlight 2",
    category: "mouse",
    price: 549,
    description: {
      en: "60g ultralight wireless gaming mouse. HERO 2 sensor with 44K DPI. The choice of esports pros.",
      ru: "Беспроводная игровая мышь 60 г. Сенсор HERO 2 с 44K DPI. Выбор киберспортсменов.",
      uk: "Бездротова ігрова миша 60 г. Сенсор HERO 2 з 44K DPI.",
      pl: "60g ultralekka bezprzewodowa mysz gamingowa. Sensor HERO 2 z 44K DPI.",
    },
    shopUrl: "https://x-kom.pl",
    tag: { en: "Esports Choice", ru: "Выбор киберспорта", uk: "Вибір кіберспорту", pl: "Wybór esportu" },
  },
];

export default peripherals;
