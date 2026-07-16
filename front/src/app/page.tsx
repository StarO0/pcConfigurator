"use client";

import { useConfiguratorStore } from "@/store/configurator-store";
import Header from "@/components/Header";
import AiChat from "@/components/AiChat";
import ManualConfigurator from "@/components/ManualConfigurator";
import { BuildCarousel } from "@/components/BuildCarousel";
import { BottleneckWarning } from "@/components/BottleneckWarning";
import ReplaceModal from "@/components/ReplaceModal";
import AuthModal from "@/components/AuthModal";
import SavedBuildsDrawer from "@/components/SavedBuildsDrawer";
import WorkspaceNav from "@/components/WorkspaceNav";
import CatalogExplorer from "@/components/CatalogExplorer";
import CompareCenter from "@/components/CompareCenter";
import AccountCenter from "@/components/AccountCenter";
import DataAdmin from "@/components/DataAdmin";
import { useWorkspaceStore } from "@/store/workspace-store";
import { AnimatePresence, motion } from "framer-motion";

export default function Home() {
  const { showResults, appMode, generationError } = useConfiguratorStore();
  const section = useWorkspaceStore((state) => state.section);

  return (
    <main className="min-h-screen flex flex-col">
      <h1 className="sr-only">AI PC Configurator - Generate optimized PC builds using Artificial Intelligence</h1>
      <Header />
      <WorkspaceNav />

      {/* Floating background orbs */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-indigo-600/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/3 -right-32 w-96 h-96 bg-violet-600/10 rounded-full blur-[128px]" />
        <div className="absolute top-2/3 left-1/2 w-64 h-64 bg-cyan-600/5 rounded-full blur-[100px]" />
      </div>

      {/* Main content area */}
      {section === "builder" && <section className="pt-8 flex-1 flex flex-col">
        {appMode === "ai" ? <AiChat /> : <ManualConfigurator />}
        {generationError && (
          <div className="mx-auto mt-4 max-w-2xl rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {generationError}
          </div>
        )}
      </section>}

      {section === "catalog" && <CatalogExplorer />}
      {section === "compare" && <CompareCenter />}
      {section === "account" && <AccountCenter />}
      {section === "data" && <DataAdmin />}

      {/* Results Section */}
      <AnimatePresence>
        {section === "builder" && showResults && (
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

          </motion.div>
        )}
      </AnimatePresence>

      {/* Modals and Drawers */}
      <ReplaceModal />
      <AuthModal />
      <SavedBuildsDrawer />

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
