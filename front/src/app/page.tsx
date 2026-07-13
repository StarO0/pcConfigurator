"use client";

import { useConfiguratorStore } from "@/store/configurator-store";
import Header from "@/components/Header";
import PromptBar from "@/components/PromptBar";
import { BuildCarousel } from "@/components/BuildCarousel";
import { BottleneckWarning } from "@/components/BottleneckWarning";
import ReplaceModal from "@/components/ReplaceModal";
import UpsellSection from "@/components/UpsellSection";
import { AnimatePresence, motion } from "framer-motion";

export default function Home() {
  const showResults = useConfiguratorStore((s) => s.showResults);

  return (
    <main className="min-h-screen flex flex-col">
      <Header />

      {/* Floating background orbs */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-indigo-600/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/3 -right-32 w-96 h-96 bg-violet-600/10 rounded-full blur-[128px]" />
        <div className="absolute top-2/3 left-1/2 w-64 h-64 bg-cyan-600/5 rounded-full blur-[100px]" />
      </div>

      {/* Prompt Section - always visible */}
      <section className="pt-8">
        <PromptBar />
      </section>

      {/* Results Section */}
      <AnimatePresence>
        {showResults && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* Bottleneck Warning */}
            <BottleneckWarning />

            {/* Build Carousel with BuildCard, AiExplanation, FpsMeter */}
            <section className="px-4 md:px-8 lg:px-16 py-8">
              <BuildCarousel />
            </section>

            {/* Divider */}
            <div className="mx-auto max-w-5xl px-4">
              <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            </div>

            {/* Upsell Peripherals */}
            <section className="px-4 md:px-8 lg:px-16 py-12">
              <UpsellSection />
            </section>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Replace Modal */}
      <ReplaceModal />

      {/* Footer */}
      <footer className="mt-auto py-8 text-center">
        <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-8" />
        <p className="text-sm text-slate-500">
          AI PC Configurator &copy; {new Date().getFullYear()} &mdash; All prices in PLN. Prices are approximate.
        </p>
      </footer>
    </main>
  );
}
