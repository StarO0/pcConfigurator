"use client";

import { useCallback, useEffect, useState } from "react";
import { ArchiveRestore, DatabaseBackup, FileSpreadsheet, Merge, Play, RefreshCw, ShieldCheck, Upload } from "lucide-react";
import { api, type ApiDuplicateGroup, type ApiParserRun, type ApiStore } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import HarvesterAdmin from "@/components/HarvesterAdmin";

type Row = Record<string, unknown>;
type ImportMode = "products" | "offers";

function key(value: string) { return value.trim().toLowerCase().replace(/[^a-z0-9а-яё]+/gi, "_").replace(/^_+|_+$/g, ""); }
function text(value: unknown) { return value == null ? "" : String(value).trim(); }
function number(value: unknown) { const parsed = Number(text(value).replace(/\s/g, "").replace(",", ".")); return Number.isFinite(parsed) ? parsed : 0; }
function boolean(value: unknown, fallback = true) { const normalized = text(value).toLowerCase(); if (!normalized) return fallback; return !["0", "false", "no", "нет", "out_of_stock"].includes(normalized); }
function slug(value: string) { return key(value).replace(/_/g, "-").slice(0, 70) || "imported"; }
function specs(row: Row) {
  const result: Record<string, unknown> = {};
  const raw = row.specs ?? row.specifications;
  if (typeof raw === "string" && raw.trim()) { try { Object.assign(result, JSON.parse(raw)); } catch { /* reported as plain fields below */ } }
  if (raw && typeof raw === "object" && !Array.isArray(raw)) Object.assign(result, raw);
  for (const [name, value] of Object.entries(row)) if (name.startsWith("spec_") && value !== "") result[name.slice(5)] = value;
  return result;
}

function productRows(rows: Row[]) {
  const errors: string[] = [];
  const seen = new Set<string>();
  const values: Row[] = [];
  rows.forEach((row, index) => {
    const name = text(row.name ?? row.title ?? row.product_name);
    const brand = text(row.brand ?? row.manufacturer) || "Unknown";
    const category = text(row.category ?? row.type);
    const sku = text(row.sku ?? row.product_sku) || `IMPORT-${slug(`${brand}-${name}`)}-${index + 1}`;
    if (!name || !category) { errors.push(`Строка ${index + 2}: нужны name/title и category`); return; }
    if (seen.has(sku)) { errors.push(`Строка ${index + 2}: повтор SKU ${sku}`); return; }
    seen.add(sku);
    values.push({ category, brand, name, sku, ean: text(row.ean ?? row.gtin) || null, mpn: text(row.mpn) || null, image_url: text(row.image_url ?? row.image) || null, performance_score: number(row.performance_score), specs: specs(row) });
  });
  return { values, errors };
}

function offerRows(rows: Row[], defaultStore: string) {
  const errors: string[] = [];
  const seen = new Set<string>();
  const values: Row[] = [];
  rows.forEach((row, index) => {
    const title = text(row.title ?? row.name ?? row.product_name);
    const storeSlug = text(row.store_slug ?? row.store) || defaultStore;
    const externalId = text(row.external_id ?? row.offer_id ?? row.sku ?? row.ean);
    const url = text(row.url ?? row.product_url);
    const price = number(row.price);
    const signature = `${storeSlug}:${externalId}`;
    if (!title || !storeSlug || !externalId || !url || price <= 0) { errors.push(`Строка ${index + 2}: нужны title, store_slug, external_id, url и price > 0`); return; }
    if (seen.has(signature)) { errors.push(`Строка ${index + 2}: повтор предложения ${signature}`); return; }
    seen.add(signature);
    values.push({ product_sku: text(row.product_sku ?? row.sku) || null, ean: text(row.ean ?? row.gtin) || null, mpn: text(row.mpn) || null, title, store_slug: storeSlug, external_id: externalId, url, price, shipping_price: number(row.shipping_price ?? row.delivery_price), currency: text(row.currency) || "PLN", in_stock: boolean(row.in_stock ?? row.availability), stock_quantity: text(row.stock_quantity) ? number(row.stock_quantity) : null, condition: text(row.condition) || "new", brand: text(row.brand) || null, category: text(row.category) || null, image_url: text(row.image_url ?? row.image) || null, specs: specs(row), source_metadata: { source: "manual_file", imported_at: new Date().toISOString() } });
  });
  return { values, errors };
}

function download(blob: Blob, filename: string) { const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url); }

export default function DataAdmin() {
  const { user, isLoggedIn, openAuthModal, ensureAccessToken, logout } = useAuthStore();
  const [stats, setStats] = useState<Record<string, number>>({});
  const [stores, setStores] = useState<ApiStore[]>([]);
  const [runs, setRuns] = useState<ApiParserRun[]>([]);
  const [duplicates, setDuplicates] = useState<ApiDuplicateGroup[]>([]);
  const [mode, setMode] = useState<ImportMode>("products");
  const [rows, setRows] = useState<Row[]>([]);
  const [fileErrors, setFileErrors] = useState<string[]>([]);
  const [selectedStore, setSelectedStore] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [collectorConsent, setCollectorConsent] = useState(false);
  const [storeForm, setStoreForm] = useState({ name: "", slug: "", baseUrl: "", sitemap: "" });

  const load = useCallback(async () => {
    if (user?.role !== "admin") return;
    const token = await ensureAccessToken(); if (!token) return;
    const [statsData, storesData, runsData, duplicateData] = await Promise.all([api.admin.stats(token), api.admin.stores(token), api.admin.parserRuns(token), api.admin.duplicates(token)]);
    setStats(statsData); setStores(storesData); setRuns(runsData.items); setDuplicates(duplicateData);
    setSelectedStore((current) => current || storesData.find((store) => store.is_active)?.slug || storesData[0]?.slug || "");
  }, [ensureAccessToken, user?.role]);
  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void load().catch((reason) => setMessage(reason instanceof Error ? reason.message : "Ошибка загрузки"));
    }, 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  if (!isLoggedIn || user?.role !== "admin") return <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-16 text-center"><ShieldCheck className="mb-5 h-12 w-12 text-emerald-400" /><h2 className="text-3xl font-bold">Локальная панель данных</h2><p className="mt-3 text-zinc-500">Для импорта и обслуживания базы нужен локальный администратор.</p><div className="mt-5 rounded-xl bg-white/5 px-5 py-3 font-mono text-sm"><p>admin@pcbuilder.app</p><p>Local-admin-123</p></div><button onClick={() => void (async () => { if (isLoggedIn) await logout(); openAuthModal("login"); })()} className="mt-6 rounded-xl bg-emerald-500 px-6 py-3 font-bold text-slate-950">Войти администратором</button></main>;

  async function selectFile(file: File) {
    setMessage("");
    try { const token = await ensureAccessToken(); if (!token) return; const preview = await api.admin.previewFile(file, token); const prepared = mode === "products" ? productRows(preview.rows) : offerRows(preview.rows, selectedStore); setRows(prepared.values); setFileErrors(prepared.errors); if (preview.truncated) setMessage(`Файл содержит ${preview.total} строк. За один раз подготовлены первые 100 000.`); }
    catch (reason) { setRows([]); setFileErrors([reason instanceof Error ? reason.message : "Не удалось прочитать файл"]); }
  }

  async function importData() {
    if (!rows.length) return;
    setBusy(true); setMessage("");
    try {
      const token = await ensureAccessToken(); if (!token) return;
      let created = 0, updated = 0, skipped = 0;
      const chunkSize = mode === "products" ? 5000 : 2000;
      for (let index = 0; index < rows.length; index += chunkSize) {
        const chunk = rows.slice(index, index + chunkSize);
        const result = mode === "products" ? await api.admin.importProducts(chunk, true, token) : await api.admin.importOffers(chunk, true, token);
        created += result.created; updated += result.updated; skipped += result.skipped;
      }
      setMessage(`Импорт завершён: создано ${created}, обновлено ${updated}, пропущено ${skipped}`); setRows([]); await load();
    } catch (reason) { setMessage(reason instanceof Error ? reason.message : "Ошибка импорта"); }
    finally { setBusy(false); }
  }

  async function normalize(dryRun: boolean) { setBusy(true); try { const token = await ensureAccessToken(); if (!token) return; const result = await api.admin.normalize(token, dryRun); setMessage(`${dryRun ? "Проверка" : "Нормализация"}: просмотрено ${result.scanned}, изменится/изменено ${result.changed}`); } catch (reason) { setMessage(reason instanceof Error ? reason.message : "Ошибка нормализации"); } finally { setBusy(false); } }
  async function mergeGroup(group: ApiDuplicateGroup, source: string) { const target = group.products[0]?.id; if (!target || target === source) return; const token = await ensureAccessToken(); if (!token) return; await api.admin.merge(source, target, token); setMessage("Дубликаты объединены"); await load(); }
  async function toggleStore(store: ApiStore) { const token = await ensureAccessToken(); if (!token) return; await api.admin.updateStore(store.id, { is_active: !store.is_active }, token); await load(); }
  async function sync(store: ApiStore) { if (!collectorConsent) { setMessage("Подтвердите проверку robots.txt и условий использования источника"); return; } setBusy(true); try { const token = await ensureAccessToken(); if (!token) return; await api.admin.updateStore(store.id, { parser_config: { ...store.parser_config, terms_confirmed: true } }, token); const run = await api.admin.syncStore(store.id, token); setMessage(`Синхронизация ${run.status}: +${run.created_count}, обновлено ${run.updated_count}, ошибок ${run.error_count}`); await load(); } catch (reason) { setMessage(reason instanceof Error ? reason.message : "Ошибка синхронизации"); } finally { setBusy(false); } }
  async function createStore() { if (!storeForm.name || !storeForm.slug || !storeForm.baseUrl) return; const token = await ensureAccessToken(); if (!token) return; await api.admin.createStore({ name: storeForm.name, slug: storeForm.slug, base_url: storeForm.baseUrl, parser_type: "catalog_acquisition", parser_config: { sitemap_urls: [storeForm.sitemap || `${storeForm.baseUrl.replace(/\/$/, "")}/sitemap.xml`], create_unmatched_products: true, require_complete_card: true, enrichment_only: false, max_pages_per_run: 25, terms_confirmed: collectorConsent } }, token); setStoreForm({ name: "", slug: "", baseUrl: "", sitemap: "" }); await load(); }
  async function backup() { const token = await ensureAccessToken(); if (!token) return; download(await api.admin.backup(token), `pc-builder-postgres-${new Date().toISOString().slice(0, 10)}.dump`); }
  async function restore(file: File) { const token = await ensureAccessToken(); if (!token) return; const result = await api.admin.restore(file, token); setMessage(result.message); }

  return <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8" data-testid="data-page">
    <div className="mb-8"><p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">Автономный data workspace</p><h2 className="mt-2 text-3xl font-bold">Импорт, очистка и источники</h2><p className="mt-2 text-sm text-zinc-500">Всё здесь работает без API-ключей. Запуск публичных коллекторов остаётся ручным и требует проверки правил конкретного сайта.</p></div>
    <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">{Object.entries(stats).map(([name, value]) => <div key={name} className="glass-card p-4"><p className="text-xs text-zinc-600">{name}</p><p className="mt-1 text-2xl font-bold text-emerald-300">{value.toLocaleString()}</p></div>)}</div>
    {message && <p className="mb-5 rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-4 text-sm text-cyan-200">{message}</p>}
    <HarvesterAdmin stores={stores} onMessage={setMessage} onRefresh={load} />
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="glass-card p-5"><div className="mb-5 flex items-center gap-2"><FileSpreadsheet className="text-cyan-400" /><h3 className="font-bold">CSV / XLSX / JSON</h3></div><div className="mb-4 flex gap-2"><button onClick={() => { setMode("products"); setRows([]); }} className={`rounded-xl px-4 py-2 text-sm ${mode === "products" ? "bg-cyan-500 text-slate-950" : "bg-white/5"}`}>Карточки товаров</button><button onClick={() => { setMode("offers"); setRows([]); }} className={`rounded-xl px-4 py-2 text-sm ${mode === "offers" ? "bg-cyan-500 text-slate-950" : "bg-white/5"}`}>Цены и наличие</button></div>{mode === "offers" && <select value={selectedStore} onChange={(event) => setSelectedStore(event.target.value)} className="mb-3 w-full rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2">{stores.map((store) => <option key={store.id} value={store.slug}>{store.name} ({store.slug})</option>)}</select>}<label className="flex cursor-pointer flex-col items-center rounded-2xl border border-dashed border-cyan-400/30 bg-cyan-500/5 p-8 text-center"><Upload className="mb-3 text-cyan-400" /><span className="font-semibold">Выберите файл</span><span className="mt-1 text-xs text-zinc-500">До 100 000 строк; импорт автоматически отправляется частями</span><input type="file" accept=".csv,.xlsx,.xlsm,.json" className="hidden" onChange={(event) => event.target.files?.[0] && void selectFile(event.target.files[0])} /></label><div className="mt-4 flex items-center justify-between"><div><p className="text-sm">Готово строк: <b>{rows.length}</b></p><p className="text-xs text-red-400">Ошибок: {fileErrors.length}</p></div><button disabled={!rows.length || busy} onClick={() => void importData()} className="rounded-xl bg-cyan-500 px-5 py-2.5 font-bold text-slate-950 disabled:opacity-30">Импортировать</button></div>{fileErrors.length > 0 && <details className="mt-3 text-xs text-red-300"><summary>Показать ошибки</summary><div className="mt-2 max-h-32 overflow-y-auto">{fileErrors.slice(0, 100).map((item) => <p key={item}>{item}</p>)}</div></details>}</section>
      <section className="glass-card p-5"><div className="mb-5 flex items-center gap-2"><RefreshCw className="text-violet-400" /><h3 className="font-bold">Нормализация и дубликаты</h3></div><div className="mb-5 flex gap-2"><button disabled={busy} onClick={() => void normalize(true)} className="rounded-xl bg-white/5 px-4 py-2 text-sm">Проверить каталог</button><button disabled={busy} onClick={() => void normalize(false)} className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-bold">Применить нормализацию</button></div><div className="max-h-80 space-y-3 overflow-y-auto">{duplicates.length ? duplicates.map((group) => <div key={group.key} className="rounded-xl bg-white/[0.03] p-3"><p className="text-xs text-zinc-600">{group.reason}: {group.key}</p>{group.products.map((product, index) => <div key={product.id} className="mt-2 flex items-center justify-between gap-3 text-sm"><span className="truncate">{index === 0 ? "Цель: " : "Дубль: "}{product.name}</span>{index > 0 && <button onClick={() => void mergeGroup(group, product.id)} className="flex items-center gap-1 rounded-lg bg-red-500/10 px-2 py-1 text-xs text-red-300"><Merge className="h-3 w-3" />Слить</button>}</div>)}</div>) : <p className="text-sm text-zinc-600">Явные дубли по нормализованному имени не найдены.</p>}</div></section>
      <section className="glass-card p-5 xl:col-span-2"><div className="mb-5 flex items-center justify-between gap-3"><div><h3 className="font-bold">Разрешённые публичные источники</h3><p className="mt-1 text-xs text-zinc-500">robots.txt, задержки, лимит страниц и отметка времени цены встроены.</p></div><label className="flex items-center gap-2 text-xs text-amber-300"><input type="checkbox" checked={collectorConsent} onChange={(event) => setCollectorConsent(event.target.checked)} />Я проверил правила источника</label></div><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{stores.map((store) => <div key={store.id} className="rounded-xl bg-white/[0.03] p-4"><div className="flex items-start justify-between"><div><p className="font-semibold">{store.name}</p><p className="text-xs text-zinc-600">{store.slug} · {store.parser_type} · {store.last_success_at ? new Date(store.last_success_at).toLocaleString() : "ещё не запускался"}</p></div><button onClick={() => void toggleStore(store)} className={`rounded-full px-2 py-1 text-[10px] ${store.is_active ? "bg-emerald-500/15 text-emerald-300" : "bg-white/5 text-zinc-500"}`}>{store.is_active ? "ON" : "OFF"}</button></div>{store.is_active && !["manual", "browser_snapshot"].includes(store.parser_type) && <button disabled={busy} onClick={() => void sync(store)} className="mt-3 flex items-center gap-2 rounded-lg bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300"><Play className="h-3 w-3" />Синхронизировать сейчас</button>}</div>)}</div><div className="mt-5 grid gap-2 md:grid-cols-4"><input placeholder="Название" value={storeForm.name} onChange={(event) => setStoreForm({ ...storeForm, name: event.target.value })} className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><input placeholder="slug" value={storeForm.slug} onChange={(event) => setStoreForm({ ...storeForm, slug: slug(event.target.value) })} className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><input placeholder="https://site.example" value={storeForm.baseUrl} onChange={(event) => setStoreForm({ ...storeForm, baseUrl: event.target.value })} className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><button onClick={() => void createStore()} className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950">Добавить sitemap</button></div></section>
      <section className="glass-card p-5"><h3 className="mb-4 font-bold">PostgreSQL backup и восстановление</h3><div className="flex flex-wrap gap-2"><button onClick={() => void backup()} className="flex items-center gap-2 rounded-xl bg-white/5 px-4 py-2 text-sm"><DatabaseBackup className="h-4 w-4" />Скачать PostgreSQL backup</button><label className="flex cursor-pointer items-center gap-2 rounded-xl bg-amber-500/10 px-4 py-2 text-sm text-amber-300"><ArchiveRestore className="h-4 w-4" />Восстановить backup<input type="file" accept=".dump" className="hidden" onChange={(event) => event.target.files?.[0] && void restore(event.target.files[0])} /></label></div><p className="mt-3 text-xs text-zinc-600">Используется pg_dump custom format. После восстановления перезапустите API и worker.</p></section>
      <section className="glass-card p-5"><h3 className="mb-4 font-bold">Журнал импорта</h3><div className="max-h-48 space-y-2 overflow-y-auto">{runs.map((run) => <div key={run.id} className="rounded-lg bg-white/[0.03] p-3 text-xs"><div className="flex justify-between"><span className={run.status === "success" ? "text-emerald-300" : run.status === "failed" ? "text-red-300" : "text-amber-300"}>{run.status}</span><span className="text-zinc-600">{new Date(run.started_at).toLocaleString()}</span></div><p className="mt-1 text-zinc-400">+{run.created_count} / ~{run.updated_count} / skipped {run.skipped_count} / errors {run.error_count}</p>{run.error_message && <p className="mt-1 text-red-300">{run.error_message}</p>}</div>)}</div></section>
    </div>
  </main>;
}
