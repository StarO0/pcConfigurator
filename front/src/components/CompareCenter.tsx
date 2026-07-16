"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, FileJson, FileText, GitCompareArrows, Link2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import type { Build } from "@/data/builds";

type CompareResult = Awaited<ReturnType<typeof api.compareBuilds>>;

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function CompareCenter() {
  const { isLoggedIn, openAuthModal, savedBuilds, refreshSavedBuilds, ensureAccessToken } = useAuthStore();
  const [leftId, setLeftId] = useState("");
  const [rightId, setRightId] = useState("");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const builds = useMemo(() => savedBuilds.filter((item) => item.build.backendId), [savedBuilds]);
  const selectedLeftId = builds.some((item) => item.id === leftId) ? leftId : (builds[0]?.id ?? "");
  const selectedRightId = builds.some((item) => item.id === rightId) ? rightId : (builds.find((item) => item.id !== selectedLeftId)?.id ?? "");
  const left = builds.find((item) => item.id === selectedLeftId)?.build;
  const right = builds.find((item) => item.id === selectedRightId)?.build;

  useEffect(() => { if (isLoggedIn) void refreshSavedBuilds(); }, [isLoggedIn, refreshSavedBuilds]);

  if (!isLoggedIn) return <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center px-4 py-20 text-center"><GitCompareArrows className="mb-5 h-12 w-12 text-violet-400" /><h2 className="text-3xl font-bold">Сравнение сохранённых сборок</h2><p className="mt-3 text-zinc-500">Сначала войдите и сохраните минимум две серверные сборки.</p><button onClick={() => openAuthModal("login")} className="mt-6 rounded-xl bg-violet-500 px-6 py-3 font-bold">Войти</button></main>;

  async function compare() {
    if (!left || !right || left.id === right.id) { setError("Выберите две разные сборки"); return; }
    setLoading(true); setError("");
    try { const token = await ensureAccessToken(); setResult(await api.compareBuilds(left, right, token)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Ошибка сравнения"); }
    finally { setLoading(false); }
  }

  async function exportJson(build: Build) {
    const token = await ensureAccessToken();
    const data = await api.exportBuild(build, token);
    downloadBlob(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), `pc-build-${build.id}.json`);
  }

  async function exportPdf() {
    if (!left || !right || !result) return;
    const { jsPDF } = await import("jspdf");
    const doc = new jsPDF();
    doc.setFontSize(18); doc.text("PC Build Comparison", 14, 18);
    doc.setFontSize(11); doc.text(`Left: ${left.name ?? left.category} - ${left.totalPrice} PLN`, 14, 30); doc.text(`Right: ${right.name ?? right.category} - ${right.totalPrice} PLN`, 14, 37);
    let y = 50;
    for (const item of result.differences) {
      const leftText = `${item.left_name ?? "-"} (${item.left_price ?? "-"} PLN)`;
      const rightText = `${item.right_name ?? "-"} (${item.right_price ?? "-"} PLN)`;
      const lines = doc.splitTextToSize(`${item.category}: ${leftText}  |  ${rightText}`, 180);
      doc.text(lines, 14, y); y += lines.length * 6 + 3;
      if (y > 275) { doc.addPage(); y = 20; }
    }
    doc.save("pc-build-comparison.pdf");
  }

  async function publish(build: Build) {
    const token = await ensureAccessToken();
    if (!token) return;
    const updated = await api.updateBuild(build, { visibility: "unlisted" }, token);
    await refreshSavedBuilds();
    if (updated.publicSlug) {
      const url = `${window.location.origin}/public/${updated.publicSlug}`;
      await navigator.clipboard.writeText(url).catch(() => undefined);
      window.alert(`Публичная ссылка скопирована:\n${url}`);
    }
  }

  return <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
    <div className="mb-8"><p className="text-sm font-semibold uppercase tracking-[0.2em] text-violet-400">Сравнение</p><h2 className="mt-2 text-3xl font-bold">Две сборки по компонентам</h2></div>
    {builds.length < 2 ? <section className="glass-card p-8 text-center text-zinc-500">Нужно сохранить минимум две сборки из AI-конфигуратора.</section> : <>
      <section className="glass-card grid gap-4 p-5 md:grid-cols-[1fr_1fr_auto]">
        <select value={selectedLeftId} onChange={(event) => setLeftId(event.target.value)} className="rounded-xl border border-white/10 bg-[#0e1622] px-4 py-3">{builds.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.build.totalPrice} PLN</option>)}</select>
        <select value={selectedRightId} onChange={(event) => setRightId(event.target.value)} className="rounded-xl border border-white/10 bg-[#0e1622] px-4 py-3">{builds.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.build.totalPrice} PLN</option>)}</select>
        <button onClick={() => void compare()} disabled={loading} className="rounded-xl bg-violet-500 px-5 py-3 font-bold disabled:opacity-50">{loading ? "Считаю..." : "Сравнить"}</button>
      </section>
      {error && <p className="mt-4 rounded-xl bg-red-500/10 p-4 text-red-300">{error}</p>}
      <div className="mt-4 flex flex-wrap gap-2">{left && <><button onClick={() => void exportJson(left)} className="flex items-center gap-2 rounded-xl bg-white/5 px-4 py-2 text-sm"><FileJson className="h-4 w-4" />JSON левой</button><button onClick={() => void publish(left)} className="flex items-center gap-2 rounded-xl bg-white/5 px-4 py-2 text-sm"><Link2 className="h-4 w-4" />Публичная ссылка</button></>}{right && <button onClick={() => void exportJson(right)} className="flex items-center gap-2 rounded-xl bg-white/5 px-4 py-2 text-sm"><Download className="h-4 w-4" />JSON правой</button>}{result && <button onClick={() => void exportPdf()} className="flex items-center gap-2 rounded-xl bg-cyan-500/15 px-4 py-2 text-sm text-cyan-300"><FileText className="h-4 w-4" />PDF сравнения</button>}</div>
      {result && <section className="glass-card mt-6 overflow-hidden"><div className="grid grid-cols-3 bg-white/[0.04] px-4 py-3 text-xs font-bold uppercase text-zinc-500"><span>Категория</span><span>{left?.name ?? "Слева"}</span><span>{right?.name ?? "Справа"}</span></div>{result.differences.map((item) => <div key={item.category} className={`grid grid-cols-3 gap-3 border-t border-white/[0.05] px-4 py-4 text-sm ${item.same_product ? "opacity-60" : "bg-violet-500/[0.03]"}`}><span className="font-semibold text-zinc-400">{item.category}</span><span>{item.left_name ?? "—"}<small className="block text-cyan-400">{item.left_price ? `${Number(item.left_price).toLocaleString()} PLN` : ""}</small></span><span>{item.right_name ?? "—"}<small className="block text-violet-400">{item.right_price ? `${Number(item.right_price).toLocaleString()} PLN` : ""}</small></span></div>)}</section>}
    </>}
  </main>;
}
