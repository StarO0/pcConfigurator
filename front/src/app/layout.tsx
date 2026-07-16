import type { Metadata } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "AI PC Configurator | Сборка ПК с помощью ИИ",
  description:
    "AI-powered PC configurator with a real catalog, compatibility checks and prices from Polish stores.",
  keywords: [
    "PC configurator",
    "AI PC builder",
    "конфигуратор ПК",
    "сборка компьютера",
    "konfigurator PC",
  ],
  openGraph: {
    title: "AI PC Configurator",
    description: "Build, validate and compare PC configurations with real catalogue data.",
    url: siteUrl,
    siteName: "AI PC Configurator",
    locale: "en_US",
    type: "website",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <body
        className="min-h-full flex flex-col bg-[var(--bg-primary)] text-white font-sans"
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}
