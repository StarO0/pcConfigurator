import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "cyrillic"],
});

export const metadata: Metadata = {
  title: "AI PC Configurator | Сборка ПК с помощью ИИ",
  description:
    "AI-powered PC configurator. Describe your ideal computer and get 5 optimized builds with real prices from Polish stores. Поддержка 4 языков: EN, RU, UK, PL.",
  keywords: [
    "PC configurator",
    "AI PC builder",
    "конфигуратор ПК",
    "сборка компьютера",
    "konfigurator PC",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full flex flex-col bg-[var(--bg-primary)] text-white font-[var(--font-inter)]" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
