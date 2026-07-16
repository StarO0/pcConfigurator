"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Cpu } from "lucide-react";
import { api } from "@/lib/api";
import type { Build } from "@/data/builds";

export default function PublicBuildPage() {
  const params = useParams<{ slug: string }>();
  const [build, setBuild] = useState<Build | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { if (params.slug) api.publicBuild(params.slug).then(setBuild).catch((reason) => setError(reason instanceof Error ? reason.message : "Сборка не найдена")); }, [params.slug]);
  return <main className="min-h-screen bg-[#0b111a] px-4 py-10 text-white"><div className="mx-auto max-w-5xl"><div className="mb-8 flex items-center gap-3"><Cpu className="text-cyan-400" /><div><p className="text-xs uppercase tracking-widest text-cyan-400">Публичная сборка</p><h1 className="text-2xl font-bold">{build?.name ?? "PC Configurator"}</h1></div></div>{error && <p className="rounded-xl bg-red-500/10 p-4 text-red-300">{error}</p>}{!build && !error && <div className="shimmer h-60 rounded-2xl" />}{build && <><section className="glass-card mb-6 flex flex-wrap items-end justify-between gap-4 p-6"><div><p className="text-zinc-500">Итоговая стоимость</p><p className="text-4xl font-bold text-cyan-300">{build.totalPrice.toLocaleString()} PLN</p></div><span className="rounded-full px-3 py-1 text-xs font-bold" style={{ color: build.badge.color, background: `${build.badge.color}22` }}>{build.badge.label.ru}</span></section><div className="grid gap-3 sm:grid-cols-2">{Object.entries(build.components).map(([category, component]) => <article key={category} className="glass-card p-4"><p className="text-xs uppercase text-zinc-600">{category}</p><h2 className="mt-1 font-semibold">{component.name}</h2><p className="mt-2 text-cyan-300">{component.price.toLocaleString()} PLN</p></article>)}</div></>}</div></main>;
}
