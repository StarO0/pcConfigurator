import { Component, ComponentCategory } from "./builds";

export type AlternativeGroup = {
  cheaper: Component[];
  upgrade: Component[];
};

const alternatives: Record<ComponentCategory, AlternativeGroup> = {
  cpu: {
    cheaper: [
      {
        id: "alt-cpu-r5-7600",
        category: "cpu",
        name: "AMD Ryzen 5 7600",
        price: 699,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 699 },
          { shop: "Morele", url: "https://morele.net", price: 719 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 709 },
        ],
        specs: { cores: "6C/12T", boost: "5.1 GHz", tdp: "65W", socket: "AM5" },
      },
      {
        id: "alt-cpu-i5-14400f",
        category: "cpu",
        name: "Intel Core i5-14400F",
        price: 599,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 599 },
          { shop: "Morele", url: "https://morele.net", price: 619 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 609 },
        ],
        specs: { cores: "6P+4E/16T", boost: "4.7 GHz", tdp: "65W", socket: "LGA1700" },
      },
    ],
    upgrade: [
      {
        id: "alt-cpu-r7-9800x3d",
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
      },
      {
        id: "alt-cpu-r9-9900x",
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
      },
    ],
  },
  gpu: {
    cheaper: [
      {
        id: "alt-gpu-rx7600",
        category: "gpu",
        name: "Sapphire Pulse RX 7600 8GB",
        price: 1149,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1149 },
          { shop: "Morele", url: "https://morele.net", price: 1179 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 1169 },
        ],
        specs: { vram: "8 GB GDDR6", boost: "2655 MHz", tdp: "150W", length: "240mm" },
      },
      {
        id: "alt-gpu-rtx4060",
        category: "gpu",
        name: "MSI GeForce RTX 4060 Ventus 2X",
        price: 1299,
        tier: "mid",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 1299 },
          { shop: "Morele", url: "https://morele.net", price: 1329 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 1319 },
        ],
        specs: { vram: "8 GB GDDR6", boost: "2460 MHz", tdp: "115W", length: "240mm" },
      },
    ],
    upgrade: [
      {
        id: "alt-gpu-rtx5070ti",
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
      },
      {
        id: "alt-gpu-rtx5080",
        category: "gpu",
        name: "MSI GeForce RTX 5080 Suprim X",
        price: 5499,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 5499 },
          { shop: "Morele", url: "https://morele.net", price: 5549 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 5579 },
        ],
        specs: { vram: "16 GB GDDR7", boost: "2617 MHz", tdp: "360W", length: "340mm" },
      },
    ],
  },
  ram: {
    cheaper: [
      {
        id: "alt-ram-16gb-5200",
        category: "ram",
        name: "Kingston Fury Beast 16GB DDR5 5200MHz",
        price: 189,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 189 },
          { shop: "Morele", url: "https://morele.net", price: 199 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 195 },
        ],
        specs: { capacity: "2x8 GB", speed: "5200 MHz", latency: "CL36", type: "DDR5" },
      },
    ],
    upgrade: [
      {
        id: "alt-ram-64gb-6000",
        category: "ram",
        name: "G.Skill Trident Z5 RGB 64GB DDR5 6000MHz CL30",
        price: 899,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 899 },
          { shop: "Morele", url: "https://morele.net", price: 929 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 919 },
        ],
        specs: { capacity: "2x32 GB", speed: "6000 MHz", latency: "CL30", type: "DDR5" },
      },
    ],
  },
  ssd: {
    cheaper: [
      {
        id: "alt-ssd-kingston-500gb",
        category: "ssd",
        name: "Kingston NV2 500GB NVMe Gen4",
        price: 139,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 139 },
          { shop: "Morele", url: "https://morele.net", price: 149 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 145 },
        ],
        specs: { capacity: "500 GB", read: "3500 MB/s", write: "2100 MB/s", interface: "PCIe 4.0" },
      },
    ],
    upgrade: [
      {
        id: "alt-ssd-990pro-2tb",
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
      },
    ],
  },
  motherboard: {
    cheaper: [
      {
        id: "alt-mb-a620-k",
        category: "motherboard",
        name: "ASUS PRIME A620M-K",
        price: 349,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 349 },
          { shop: "Morele", url: "https://morele.net", price: 359 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 355 },
        ],
        specs: { socket: "AM5", chipset: "A620", ram: "DDR5", formFactor: "mATX" },
      },
    ],
    upgrade: [
      {
        id: "alt-mb-x870-ace",
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
      },
    ],
  },
  psu: {
    cheaper: [
      {
        id: "alt-psu-cv550",
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
      },
    ],
    upgrade: [
      {
        id: "alt-psu-hx1000",
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
      },
    ],
  },
  case: {
    cheaper: [
      {
        id: "alt-case-q300l",
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
      },
    ],
    upgrade: [
      {
        id: "alt-case-torrent",
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
      },
    ],
  },
  cooler: {
    cheaper: [
      {
        id: "alt-cooler-gammaxx-400",
        category: "cooler",
        name: "Deepcool GAMMAXX 400 V2",
        price: 89,
        tier: "budget",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 89 },
          { shop: "Morele", url: "https://morele.net", price: 99 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 95 },
        ],
        specs: { type: "Tower", height: "155mm", tdp: "180W", fan: "120mm" },
      },
    ],
    upgrade: [
      {
        id: "alt-cooler-arctic-420",
        category: "cooler",
        name: "Arctic Liquid Freezer III 420",
        price: 549,
        tier: "enthusiast",
        shopLinks: [
          { shop: "X-Kom", url: "https://x-kom.pl", price: 549 },
          { shop: "Morele", url: "https://morele.net", price: 569 },
          { shop: "Komputronik", url: "https://komputronik.pl", price: 559 },
        ],
        specs: { type: "AIO Liquid 420mm", height: "53mm", tdp: "350W", fan: "3x 140mm" },
      },
    ],
  },
};

export default alternatives;
