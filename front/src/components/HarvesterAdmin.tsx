"use client";
/* eslint-disable @next/next/no-img-element -- staging previews accept arbitrary source hosts */

import { useCallback, useEffect, useState } from "react";
import {
  Check,
  ClipboardPaste,
  DatabaseZap,
  Download,
  Globe2,
  ListPlus,
  RefreshCw,
  Upload,
  X,
} from "lucide-react";
import {
  api,
  type ApiEnrichmentStatus,
  type ApiHarvestDashboard,
  type ApiHarvestRecord,
  type ApiStore,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

type Props = {
  stores: ApiStore[];
  onMessage: (message: string) => void;
  onRefresh: () => Promise<void>;
};

const DASHBOARD_LABELS: Record<keyof ApiHarvestDashboard, string> = {
  records: "Записей staging",
  accepted: "Принято",
  pending: "Ждёт проверки",
  rejected: "Отклонено",
  errors: "Ошибок",
  queued_urls: "URL в очереди",
  products: "Товаров",
  products_with_images: "С фото",
  image_coverage_percent: "Покрытие фото, %",
  active_offers: "Активных цен",
  snapshot_offers: "Цен-снимков",
  source_count: "Источников",
};

const EMPTY_SOURCE = {
  name: "",
  slug: "",
  baseUrl: "",
  parserType: "catalog_acquisition",
  feedUrl: "",
  selectors: "{}",
  termsConfirmed: false,
};

function sourceSlug(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
}

function resultText(result: {
  accepted: number;
  pending: number;
  products_created: number;
  offers_created: number;
  offers_updated: number;
}) {
  return `Принято ${result.accepted}; staging ${result.pending}; новых товаров ${result.products_created}; новых/обновлённых цен ${result.offers_created + result.offers_updated}`;
}

export default function HarvesterAdmin({ stores, onMessage, onRefresh }: Props) {
  const { ensureAccessToken } = useAuthStore();
  const [dashboard, setDashboard] = useState<ApiHarvestDashboard | null>(null);
  const [enrichment, setEnrichment] = useState<ApiEnrichmentStatus | null>(null);
  const [pending, setPending] = useState<ApiHarvestRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [html, setHtml] = useState("");
  const [pageUrl, setPageUrl] = useState("");
  const [htmlSource, setHtmlSource] = useState({ name: "Ручной HTML", slug: "manual-html" });
  const [selectors, setSelectors] = useState("{}");
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [source, setSource] = useState(EMPTY_SOURCE);
  const [queueStore, setQueueStore] = useState("");
  const [queueText, setQueueText] = useState("");
  const [enrichmentStore, setEnrichmentStore] = useState("");
  const [enrichmentPages, setEnrichmentPages] = useState(25);
  const [enrichmentConsent, setEnrichmentConsent] = useState(false);

  const load = useCallback(async () => {
    const token = await ensureAccessToken();
    if (!token) return;
    const [stats, records, enrichmentStats] = await Promise.all([
      api.admin.harvesterDashboard(token),
      api.admin.harvestRecords(token),
      api.admin.enrichmentStatus(token),
    ]);
    setDashboard(stats);
    setPending(records.items);
    setEnrichment(enrichmentStats);
    setEnrichmentStore((current) => current || enrichmentStats.stores[0]?.id || "");
  }, [ensureAccessToken]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load().catch(() => undefined), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  useEffect(() => {
    if (!queueStore && stores.length) {
      const timeout = window.setTimeout(() => setQueueStore(stores[0].slug), 0);
      return () => window.clearTimeout(timeout);
    }
  }, [queueStore, stores]);

  async function withBusy(action: () => Promise<void>) {
    setBusy(true);
    try {
      await action();
      await Promise.all([load(), onRefresh()]);
    } catch (reason) {
      onMessage(reason instanceof Error ? reason.message : "Операция Catalog Harvester не выполнена");
    } finally {
      setBusy(false);
    }
  }

  async function importCollector(file: File) {
    await withBusy(async () => {
      const token = await ensureAccessToken();
      if (!token) return;
      const parsed: unknown = JSON.parse(await file.text());
      if (!parsed || typeof parsed !== "object" || !("items" in parsed)) {
        throw new Error("Это не JSON от PC Catalog Collector: отсутствует items[]");
      }
      const result = await api.admin.browserImport(parsed as Record<string, unknown>, token);
      onMessage(`Browser Collector: ${resultText(result)}`);
    });
  }

  function htmlPayload() {
    if (!pageUrl || !html) throw new Error("Укажите URL и вставьте HTML страницы");
    return {
      html,
      url: pageUrl,
      store_slug: sourceSlug(htmlSource.slug),
      source_name: htmlSource.name,
      selectors: JSON.parse(selectors) as Record<string, unknown>,
      create_products: true,
      auto_accept: true,
    };
  }

  async function previewHtml() {
    await withBusy(async () => {
      const token = await ensureAccessToken();
      if (!token) return;
      const payload = htmlPayload();
      const result = await api.admin.extractHtml(payload, token);
      setPreview(result);
      onMessage("HTML разобран. Проверьте найденные поля и нажмите «Импортировать».");
    });
  }

  async function importHtml() {
    await withBusy(async () => {
      const token = await ensureAccessToken();
      if (!token) return;
      const result = await api.admin.importHtml(htmlPayload(), token);
      onMessage(`HTML import: ${resultText(result)}`);
      setPreview(null);
      setHtml("");
    });
  }

  async function review(record: ApiHarvestRecord, approve: boolean) {
    await withBusy(async () => {
      const token = await ensureAccessToken();
      if (!token) return;
      if (approve) {
        const result = await api.admin.approveHarvest(record.id, token);
        onMessage(`Запись подтверждена. ${resultText(result)}`);
      } else {
        const result = await api.admin.rejectHarvest(record.id, token);
        onMessage(result.message);
      }
    });
  }

  async function createSource() {
    await withBusy(async () => {
      if (!source.name || !source.slug || !source.baseUrl) {
        throw new Error("Для источника нужны название, slug и базовый URL");
      }
      const token = await ensureAccessToken();
      if (!token) return;
      const config: Record<string, unknown> = {
        terms_confirmed: source.termsConfirmed,
        create_unmatched_products: source.parserType === "catalog_acquisition",
        require_complete_card: source.parserType === "catalog_acquisition",
        schedule_minutes: 360,
        max_pages_per_run: 25,
      };
      if (["jsonld_sitemap", "catalog_acquisition"].includes(source.parserType)) {
        config.sitemap_urls = [source.feedUrl || `${source.baseUrl.replace(/\/$/, "")}/sitemap.xml`];
      } else if (["xml", "yml", "json", "csv"].includes(source.parserType)) {
        config.url = source.feedUrl;
      } else if (source.parserType === "html_selector") {
        config.urls = source.feedUrl.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
        config.selectors = JSON.parse(source.selectors) as Record<string, unknown>;
      }
      await api.admin.createStore(
        {
          name: source.name,
          slug: sourceSlug(source.slug),
          base_url: source.baseUrl,
          parser_type: source.parserType,
          parser_config: config,
        },
        token,
      );
      setSource(EMPTY_SOURCE);
      onMessage("Источник добавлен. Автообход работает только после подтверждения правил сайта.");
    });
  }

  async function addQueue() {
    await withBusy(async () => {
      const urls = queueText.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
      if (!queueStore || !urls.length) throw new Error("Выберите источник и добавьте URL по одному на строку");
      const token = await ensureAccessToken();
      if (!token) return;
      const result = await api.admin.queueUrls(queueStore, urls, token);
      onMessage(result.message);
      setQueueText("");
    });
  }

  async function processSelectedQueue() {
    await withBusy(async () => {
      const store = stores.find((item) => item.slug === queueStore);
      if (!store) throw new Error("Источник очереди не найден");
      const token = await ensureAccessToken();
      if (!token) return;
      const result = await api.admin.processQueue(store.id, token);
      onMessage(result.message);
    });
  }

  async function runDue() {
    await withBusy(async () => {
      const token = await ensureAccessToken();
      if (!token) return;
      const result = await api.admin.runDue(token);
      onMessage(`Расписание: проверено ${result.checked}, запущено ${result.started}, пропущено ${result.skipped}`);
    });
  }

  async function runEnrichment() {
    await withBusy(async () => {
      if (!enrichmentStore) throw new Error("Источник наполнения не выбран");
      if (!enrichmentConsent) {
        throw new Error("Сначала подтвердите проверку robots.txt и условий выбранного магазина");
      }
      const token = await ensureAccessToken();
      if (!token) return;
      const run = await api.admin.runEnrichment(
        enrichmentStore,
        enrichmentPages,
        enrichmentConsent,
        token,
      );
      const batch = enrichment?.stores.find((store) => store.id === enrichmentStore)?.name ?? "магазина";
      onMessage(
        `${batch}: ${run.status}; добавлено ${run.created_count}, обновлено ${run.updated_count}, неоднозначных/повторов ${run.skipped_count}, ошибок ${run.error_count}${run.error_message ? `. Причина: ${run.error_message}` : ""}`,
      );
    });
  }

  const selectedEnrichment = enrichment?.stores.find((store) => store.id === enrichmentStore);

  return (
    <section className="glass-card mb-6 p-5 xl:p-6" data-testid="harvester-admin">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">Catalog Harvester v6</p>
          <h3 className="mt-1 text-xl font-bold">Универсальное наполнение без API-ключей</h3>
          <p className="mt-2 max-w-3xl text-sm text-zinc-500">JSON-LD, sitemap, XML/YML, CSV/JSON, CSS-селекторы, вставленный HTML и сбор из открытой страницы браузера проходят через staging и дедупликацию.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a href="/pc-catalog-collector.zip" download className="flex items-center gap-2 rounded-xl bg-cyan-500/10 px-4 py-2 text-sm text-cyan-300"><Download className="h-4 w-4" />Расширение</a>
          <button disabled={busy} onClick={() => void runDue()} className="flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 disabled:opacity-40"><RefreshCw className="h-4 w-4" />Запустить расписание</button>
        </div>
      </div>

      {dashboard && <div className="mt-5 grid gap-2 sm:grid-cols-3 lg:grid-cols-6">{(Object.keys(DASHBOARD_LABELS) as Array<keyof ApiHarvestDashboard>).map((key) => <div key={key} className="rounded-xl bg-white/[0.035] p-3"><p className="text-[10px] text-zinc-600">{DASHBOARD_LABELS[key]}</p><p className="mt-1 text-lg font-bold text-emerald-300">{dashboard[key].toLocaleString("ru-RU")}</p></div>)}</div>}

      {enrichment && <div className="mt-6 rounded-2xl border border-cyan-400/15 bg-cyan-500/[0.04] p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Живое наполнение каталога</p>
            <h4 className="mt-1 text-lg font-bold">Open Icecat + цены польских магазинов</h4>
            <p className="mt-1 text-xs text-zinc-500">Магазин даёт цену в PLN и GTIN/MPN, Open Icecat — каноническое название, характеристики и официальные фото. Новая карточка публикуется только целиком: цена, HTTPS-фото, категория, бренд и устойчивый идентификатор.</p>
          </div>
          <div className="min-w-56 text-right"><p className="text-2xl font-bold text-cyan-300">{enrichment.coverage_percent.toLocaleString("ru-RU")} %</p><p className="text-xs text-zinc-500">{enrichment.products_complete.toLocaleString("ru-RU")} из {enrichment.products.toLocaleString("ru-RU")} с фото и ценой</p></div>
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/5"><div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400" style={{ width: `${Math.max(enrichment.coverage_percent, 0.2)}%` }} /></div>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
          <div className="rounded-xl bg-black/15 p-3"><p className="text-[10px] text-zinc-600">С фото</p><p className="font-bold">{enrichment.products_with_images.toLocaleString("ru-RU")}</p></div>
          <div className="rounded-xl bg-black/15 p-3"><p className="text-[10px] text-zinc-600">С предложениями</p><p className="font-bold">{enrichment.products_with_offers.toLocaleString("ru-RU")}</p></div>
          <div className="rounded-xl bg-black/15 p-3"><p className="text-[10px] text-zinc-600">В нескольких магазинах</p><p className="font-bold">{enrichment.products_with_multiple_stores.toLocaleString("ru-RU")}</p></div>
          <div className="rounded-xl bg-black/15 p-3"><p className="text-[10px] text-zinc-600">Без цены</p><p className="font-bold text-amber-300">{enrichment.missing_offers.toLocaleString("ru-RU")}</p></div>
          <div className="rounded-xl bg-black/15 p-3"><p className="text-[10px] text-zinc-600">Неоднозначные</p><p className="font-bold text-violet-300">{enrichment.pending_ambiguous.toLocaleString("ru-RU")}</p></div>
        </div>
        <div className="mt-4 grid gap-2 md:grid-cols-[1fr_auto_auto]">
          <select value={enrichmentStore} onChange={(event) => setEnrichmentStore(event.target.value)} className="rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2.5 text-sm">
            {enrichment.stores.map((store) => <option key={store.id} value={store.id}>{store.name} · просмотрено {store.crawl_offset.toLocaleString("ru-RU")} / {store.discovered_urls ? store.discovered_urls.toLocaleString("ru-RU") : "каталог ещё не прочитан"}</option>)}
          </select>
          <select value={enrichmentPages} onChange={(event) => setEnrichmentPages(Number(event.target.value))} className="rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2.5 text-sm"><option value={10}>10 страниц</option><option value={25}>25 страниц</option><option value={50}>50 страниц</option><option value={100}>100 страниц</option></select>
          <button disabled={busy || !enrichment.stores.length} onClick={() => void runEnrichment()} className="rounded-xl bg-cyan-400 px-5 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-30">Обработать пакет</button>
        </div>
        <label className="mt-3 flex items-start gap-2 text-xs text-amber-300"><input type="checkbox" checked={enrichmentConsent} onChange={(event) => setEnrichmentConsent(event.target.checked)} className="mt-0.5" /><span>Я проверил robots.txt и условия выбранного магазина. Парсер соблюдает запреты, задержку и лимит страниц.</span></label>
        {selectedEnrichment?.last_error_message && <p className="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-300">Последняя ошибка {selectedEnrichment.name}: {selectedEnrichment.last_error_message}</p>}
      </div>}

      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <div className="rounded-2xl border border-white/5 bg-black/10 p-4">
          <div className="mb-3 flex items-center gap-2"><Globe2 className="h-5 w-5 text-cyan-400" /><h4 className="font-semibold">Browser Collector</h4></div>
          <p className="mb-4 text-xs text-zinc-500">Расширение читает только открытую вами карточку, сохраняет JSON локально и обходит CORS/динамическую разметку без внешнего сервиса.</p>
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-cyan-400/30 bg-cyan-500/5 p-5 text-sm text-cyan-200"><Upload className="h-4 w-4" />Загрузить JSON расширения<input type="file" accept=".json,application/json" className="hidden" onChange={(event) => event.target.files?.[0] && void importCollector(event.target.files[0])} /></label>
        </div>

        <div className="rounded-2xl border border-white/5 bg-black/10 p-4">
          <div className="mb-3 flex items-center gap-2"><ClipboardPaste className="h-5 w-5 text-violet-400" /><h4 className="font-semibold">Вставить HTML карточки</h4></div>
          <div className="grid gap-2 sm:grid-cols-2"><input value={htmlSource.name} onChange={(event) => setHtmlSource({ ...htmlSource, name: event.target.value })} placeholder="Название источника" className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><input value={htmlSource.slug} onChange={(event) => setHtmlSource({ ...htmlSource, slug: sourceSlug(event.target.value) })} placeholder="source-slug" className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /></div>
          <input value={pageUrl} onChange={(event) => setPageUrl(event.target.value)} placeholder="https://shop.example/product" className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" />
          <textarea value={html} onChange={(event) => setHtml(event.target.value)} placeholder="HTML страницы" rows={4} className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 p-3 font-mono text-xs" />
          <details className="mt-2 text-xs text-zinc-500"><summary>CSS-селекторы, если JSON-LD нет</summary><textarea value={selectors} onChange={(event) => setSelectors(event.target.value)} rows={3} className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 p-3 font-mono" placeholder='{"title":"h1","price":".price","image":{"selector":"img.main","attribute":"src"}}' /></details>
          <div className="mt-3 flex gap-2"><button disabled={busy} onClick={() => void previewHtml()} className="rounded-xl bg-white/5 px-4 py-2 text-sm">Проверить</button><button disabled={busy || !preview} onClick={() => void importHtml()} className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-bold disabled:opacity-30">Импортировать</button></div>
          {preview && <p className="mt-3 truncate text-xs text-emerald-300">Найдено: {String(preview.title)} · {String(preview.price ?? "без цены")}</p>}
        </div>

        <div className="rounded-2xl border border-white/5 bg-black/10 p-4 xl:col-span-2">
          <div className="mb-3 flex items-center gap-2"><DatabaseZap className="h-5 w-5 text-amber-400" /><h4 className="font-semibold">Новый автоматический источник</h4></div>
          <div className="grid gap-2 md:grid-cols-3"><input value={source.name} onChange={(event) => setSource({ ...source, name: event.target.value })} placeholder="Название" className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><input value={source.slug} onChange={(event) => setSource({ ...source, slug: sourceSlug(event.target.value) })} placeholder="source-slug" className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><input value={source.baseUrl} onChange={(event) => setSource({ ...source, baseUrl: event.target.value })} placeholder="https://shop.example" className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><select value={source.parserType} onChange={(event) => setSource({ ...source, parserType: event.target.value })} className="rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2 text-sm"><option value="catalog_acquisition">Готовые карточки: магазин + Open Icecat</option><option value="jsonld_sitemap">Sitemap + JSON-LD</option><option value="xml">XML feed</option><option value="yml">YML feed</option><option value="json">JSON feed</option><option value="csv">CSV feed</option><option value="html_selector">HTML + CSS selectors</option></select><textarea value={source.feedUrl} onChange={(event) => setSource({ ...source, feedUrl: event.target.value })} placeholder="URL sitemap/feed или URL карточек по одному на строку" rows={2} className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm md:col-span-2" /></div>
          {source.parserType === "html_selector" && <textarea value={source.selectors} onChange={(event) => setSource({ ...source, selectors: event.target.value })} rows={2} className="mt-2 w-full rounded-xl border border-white/10 bg-black/20 p-3 font-mono text-xs" placeholder='{"title":"h1","price":".price"}' />}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3"><label className="flex items-center gap-2 text-xs text-amber-300"><input type="checkbox" checked={source.termsConfirmed} onChange={(event) => setSource({ ...source, termsConfirmed: event.target.checked })} />Я проверил robots.txt и условия автоматического обхода</label><button disabled={busy} onClick={() => void createSource()} className="rounded-xl bg-amber-500 px-4 py-2 text-sm font-bold text-slate-950">Добавить источник</button></div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-black/10 p-4 xl:col-span-2">
          <div className="mb-3 flex items-center gap-2"><ListPlus className="h-5 w-5 text-emerald-400" /><h4 className="font-semibold">Очередь URL</h4></div>
          <div className="grid gap-2 md:grid-cols-[240px_1fr_auto_auto]"><select value={queueStore} onChange={(event) => setQueueStore(event.target.value)} className="rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2 text-sm">{stores.map((store) => <option key={store.id} value={store.slug}>{store.name}</option>)}</select><textarea value={queueText} onChange={(event) => setQueueText(event.target.value)} rows={2} placeholder="URL карточек по одному на строку" className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm" /><button disabled={busy} onClick={() => void addQueue()} className="rounded-xl bg-white/5 px-4 py-2 text-sm">В очередь</button><button disabled={busy} onClick={() => void processSelectedQueue()} className="rounded-xl bg-emerald-500/15 px-4 py-2 text-sm text-emerald-300">Обработать</button></div>
        </div>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between"><h4 className="font-semibold">Спорные совпадения ({pending.length})</h4><button onClick={() => void load()} className="text-xs text-zinc-500 hover:text-cyan-300">Обновить</button></div>
        <div className="max-h-72 space-y-2 overflow-y-auto">{pending.length ? pending.map((record) => <div key={record.id} className="grid gap-3 rounded-xl bg-white/[0.03] p-3 sm:grid-cols-[56px_1fr_auto] sm:items-center">{record.image_url ? <img src={record.image_url} alt="" className="h-14 w-14 rounded-lg bg-white object-contain" referrerPolicy="no-referrer" /> : <div className="h-14 w-14 rounded-lg bg-white/5" />}<div className="min-w-0"><p className="truncate text-sm font-semibold">{record.title}</p><p className="text-xs text-zinc-600">{record.store_slug} · {record.category ?? "категория не определена"} · match {record.match_confidence.toFixed(0)}% ({record.match_method}) · quality {record.quality_score.toFixed(0)}%</p></div><div className="flex gap-2"><button title="Принять" onClick={() => void review(record, true)} className="rounded-lg bg-emerald-500/15 p-2 text-emerald-300"><Check className="h-4 w-4" /></button><button title="Отклонить" onClick={() => void review(record, false)} className="rounded-lg bg-red-500/15 p-2 text-red-300"><X className="h-4 w-4" /></button></div></div>) : <p className="rounded-xl bg-white/[0.025] p-4 text-sm text-zinc-600">Очередь проверки пуста: уверенные записи опубликованы автоматически.</p>}</div>
      </div>
    </section>
  );
}
