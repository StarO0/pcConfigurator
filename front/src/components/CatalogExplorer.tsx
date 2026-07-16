"use client";
/* eslint-disable @next/next/no-img-element -- product images come from imported external catalogues */

import { useEffect, useMemo, useState } from "react";
import {
  BellPlus,
  Check,
  ChevronLeft,
  ChevronRight,
  GitCompareArrows,
  Heart,
  History,
  Search,
  Store,
  X,
} from "lucide-react";
import {
  api,
  ApiError,
  type ApiPricePoint,
  type ApiProduct,
  type ApiProductCompare,
} from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

const LIMIT = 48;
const MAX_COMPARE = 4;
const CATEGORY_NAMES: Record<string, string> = {
  cpu: "Процессоры",
  gpu: "Видеокарты",
  motherboard: "Материнские платы",
  ram: "Оперативная память",
  storage: "Накопители",
  psu: "Блоки питания",
  case: "Корпуса",
  cooler: "Охлаждение",
  monitor: "Мониторы",
  keyboard: "Клавиатуры",
  mouse: "Мыши",
  headphones: "Наушники",
  headset: "Гарнитуры",
  webcam: "Веб-камеры",
  ups: "ИБП",
};

function errorText(error: unknown) {
  return error instanceof ApiError
    ? error.message
    : error instanceof Error
      ? error.message
      : "Ошибка запроса";
}

function bestPrice(product: ApiProduct): number | null {
  const prices = product.offers
    .filter((offer) => offer.in_stock && offer.currency === "PLN")
    .map((offer) => Number(offer.effective_price));
  return prices.length ? Math.min(...prices) : null;
}

function displaySpec(value: unknown): string {
  if (value === undefined || value === null || value === "") return "—";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  if (typeof value === "boolean") return value ? "Да" : "Нет";
  return String(value);
}

function ProductHistory({ product, onClose }: { product: ApiProduct; onClose: () => void }) {
  const [points, setPoints] = useState<ApiPricePoint[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api
      .productPriceHistory(product.id, 365)
      .then((data) => {
        if (active) setPoints(data.points);
      })
      .catch((reason) => {
        if (active) setError(errorText(reason));
      });
    return () => {
      active = false;
    };
  }, [product.id]);

  const max = Math.max(
    ...points.map((point) => Number(point.price) + Number(point.shipping_price)),
    1,
  );

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <section
        className="glass-card max-h-[85vh] w-full max-w-3xl overflow-y-auto p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-cyan-400">История цены</p>
            <h2 className="mt-1 text-xl font-bold">{product.name}</h2>
          </div>
          <button onClick={onClose} className="rounded-lg bg-white/5 px-3 py-2 text-sm text-zinc-400">
            Закрыть
          </button>
        </div>
        {error && <p className="text-red-400">{error}</p>}
        {!error && !points.length && (
          <p className="text-zinc-500">История появится после первого импорта или изменения цены.</p>
        )}
        <div className="space-y-2">
          {points.map((point, index) => {
            const value = Number(point.price) + Number(point.shipping_price);
            return (
              <div
                key={`${point.offer_id}-${point.recorded_at}-${index}`}
                className="grid grid-cols-[120px_1fr_100px] items-center gap-3 text-xs"
              >
                <span className="truncate text-zinc-500">{point.store_name}</span>
                <div className="h-6 overflow-hidden rounded bg-white/5">
                  <div
                    className="h-full rounded bg-gradient-to-r from-cyan-500/50 to-violet-500/70"
                    style={{ width: `${Math.max((value / max) * 100, 3)}%` }}
                  />
                </div>
                <span className="text-right font-semibold text-cyan-300">
                  {value.toLocaleString()} {point.currency}
                </span>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function ProductComparison({ result, onClose }: { result: ApiProductCompare; onClose: () => void }) {
  const keys = result.spec_keys.slice(0, 30);
  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/80 p-3 sm:p-6"
      onClick={onClose}
    >
      <section
        className="glass-card max-h-[92vh] w-full max-w-7xl overflow-auto p-4 sm:p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">
              Сравнение товаров
            </p>
            <h2 className="mt-1 text-2xl font-bold">
              {result.common_category
                ? CATEGORY_NAMES[result.common_category] ?? result.common_category
                : "Разные категории"}
            </h2>
          </div>
          <button onClick={onClose} className="rounded-xl bg-white/5 p-2 text-zinc-400">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div
          className="grid min-w-[760px] gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10"
          style={{ gridTemplateColumns: `180px repeat(${result.products.length}, minmax(190px, 1fr))` }}
        >
          <div className="bg-[#0b111b] p-4 text-xs font-bold uppercase text-zinc-500">Параметр</div>
          {result.products.map((product) => (
            <div key={product.id} className="bg-[#0b111b] p-4">
              <div className="mb-3 flex h-28 items-center justify-center rounded-xl bg-white p-2">
                <img
                  src={product.image_url || "/product-fallback.svg"}
                  alt={product.name}
                  className="h-full w-full object-contain"
                  referrerPolicy="no-referrer"
                />
              </div>
              <p className="text-xs text-zinc-500">{product.brand}</p>
              <h3 className="mt-1 text-sm font-semibold leading-snug">{product.name}</h3>
            </div>
          ))}

          <div className="bg-[#0e1622] p-4 text-sm font-semibold text-zinc-400">Лучшая цена</div>
          {result.products.map((product) => {
            const price = bestPrice(product);
            const winner = result.lowest_effective_price_product_id === product.id;
            return (
              <div key={`price-${product.id}`} className={`bg-[#0e1622] p-4 ${winner ? "text-emerald-300" : ""}`}>
                <span className="font-bold">{price === null ? "—" : `${price.toLocaleString("pl-PL")} PLN`}</span>
                {winner && <Check className="ml-2 inline h-4 w-4" />}
              </div>
            );
          })}

          <div className="bg-[#0b111b] p-4 text-sm font-semibold text-zinc-400">Производительность</div>
          {result.products.map((product) => {
            const winner = result.highest_performance_product_id === product.id;
            return (
              <div key={`performance-${product.id}`} className={`bg-[#0b111b] p-4 ${winner ? "text-cyan-300" : ""}`}>
                <span className="font-bold">{product.performance_score.toFixed(1)}</span>
                {winner && <Check className="ml-2 inline h-4 w-4" />}
              </div>
            );
          })}

          {keys.map((key, index) => (
            <div key={`row-${key}`} className="contents">
              <div className={`${index % 2 ? "bg-[#0e1622]" : "bg-[#0b111b]"} p-4 text-xs font-semibold text-zinc-500`}>
                {key}
              </div>
              {result.products.map((product) => (
                <div
                  key={`${product.id}-${key}`}
                  className={`${index % 2 ? "bg-[#0e1622]" : "bg-[#0b111b]"} p-4 text-sm text-zinc-300`}
                >
                  {displaySpec(product.specs[key])}
                </div>
              ))}
            </div>
          ))}
        </div>
        {result.spec_keys.length > keys.length && (
          <p className="mt-4 text-xs text-zinc-600">
            Показаны первые {keys.length} характеристик из {result.spec_keys.length}.
          </p>
        )}
      </section>
    </div>
  );
}

export default function CatalogExplorer() {
  const { isLoggedIn, ensureAccessToken, openAuthModal } = useAuthStore();
  const [products, setProducts] = useState<ApiProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [category, setCategory] = useState("");
  const [brand, setBrand] = useState("");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [inStock, setInStock] = useState(true);
  const [sort, setSort] = useState<"name" | "price" | "performance" | "newest">("price");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [historyProduct, setHistoryProduct] = useState<ApiProduct | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareResult, setCompareResult] = useState<ApiProductCompare | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setPage(0);
      setLoading(true);
      setQuery(search.trim().length >= 2 ? search.trim() : "");
    }, 350);
    return () => window.clearTimeout(timeout);
  }, [search]);

  useEffect(() => {
    api.productCategories().then(setCategories).catch(() => undefined);
  }, []);

  useEffect(() => {
    api.productBrands(category || undefined).then(setBrands).catch(() => setBrands([]));
  }, [category]);

  useEffect(() => {
    let active = true;
    api
      .products({ search: query, category, brand, inStock, sort, limit: LIMIT, offset: page * LIMIT })
      .then((data) => {
        if (active) {
          setProducts(data.items);
          setTotal(data.total);
          setError("");
        }
      })
      .catch((reason) => {
        if (active) setError(errorText(reason));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [query, category, brand, inStock, sort, page]);

  useEffect(() => {
    if (!isLoggedIn) {
      const timeout = window.setTimeout(() => setFavorites(new Set()), 0);
      return () => window.clearTimeout(timeout);
    }
    void (async () => {
      const token = await ensureAccessToken();
      if (!token) return;
      const data = await api.favoriteProducts(token).catch(() => null);
      if (data) setFavorites(new Set(data.items.map((product) => product.id)));
    })();
  }, [ensureAccessToken, isLoggedIn]);

  const pages = Math.max(1, Math.ceil(total / LIMIT));
  const range = useMemo(
    () => `${total ? page * LIMIT + 1 : 0}–${Math.min((page + 1) * LIMIT, total)}`,
    [page, total],
  );
  const compareProducts = compareIds
    .map((id) => products.find((product) => product.id === id))
    .filter((product): product is ApiProduct => Boolean(product));

  async function toggleFavorite(product: ApiProduct) {
    if (!isLoggedIn) {
      openAuthModal("login");
      return;
    }
    const token = await ensureAccessToken();
    if (!token) return;
    const next = !favorites.has(product.id);
    await api.setFavorite(product.id, next, token);
    setFavorites((current) => {
      const value = new Set(current);
      if (next) value.add(product.id);
      else value.delete(product.id);
      return value;
    });
  }

  function toggleCompare(productId: string) {
    setCompareIds((current) => {
      if (current.includes(productId)) return current.filter((id) => id !== productId);
      if (current.length >= MAX_COMPARE) {
        setError(`Можно сравнить максимум ${MAX_COMPARE} товара`);
        return current;
      }
      setError("");
      return [...current, productId];
    });
  }

  async function runCompare() {
    if (compareIds.length < 2) {
      setError("Выберите минимум два товара");
      return;
    }
    setCompareLoading(true);
    setError("");
    try {
      setCompareResult(await api.compareProducts(compareIds));
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setCompareLoading(false);
    }
  }

  async function createAlert(product: ApiProduct) {
    if (!isLoggedIn) {
      openAuthModal("login");
      return;
    }
    const cheapest = bestPrice(product) ?? 0;
    const raw = window.prompt(
      "Целевая цена в PLN",
      cheapest ? String(Math.floor(cheapest * 0.9)) : "1000",
    );
    if (!raw) return;
    const value = Number(raw.replace(",", "."));
    if (!Number.isFinite(value) || value <= 0) return;
    const token = await ensureAccessToken();
    if (token) await api.createPriceAlert(product.id, value, token);
  }

  return (
    <main
      className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8"
      data-testid="catalog-page"
    >
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">Локальный каталог</p>
        <h2 className="mt-2 text-3xl font-bold">
          {inStock ? "Товары с активной ценой" : "Все каталожные карточки"}: {total.toLocaleString("ru-RU")}
        </h2>
        <p className="mt-2 text-sm text-zinc-500">
          В каталог публикуются только проверенные карточки. Цены и наличие хранятся отдельно от
          характеристик товара и обновляются фоновыми задачами.
        </p>
      </div>

      <section className="glass-card mb-6 grid gap-3 p-4 md:grid-cols-[2fr_1fr_1fr_1fr_auto]">
        <label className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-zinc-600" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Название, SKU, MPN..."
            className="w-full rounded-xl border border-white/10 bg-black/20 py-2.5 pl-9 pr-3 text-sm"
          />
        </label>
        <select
          value={category}
          onChange={(event) => {
            setLoading(true);
            setPage(0);
            setBrand("");
            setCategory(event.target.value);
          }}
          className="rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2.5 text-sm"
        >
          <option value="">Все категории</option>
          {categories.map((item) => (
            <option key={item} value={item}>
              {CATEGORY_NAMES[item] ?? item}
            </option>
          ))}
        </select>
        <select
          value={brand}
          onChange={(event) => {
            setLoading(true);
            setPage(0);
            setBrand(event.target.value);
          }}
          className="rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2.5 text-sm"
        >
          <option value="">Все бренды</option>
          {brands.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(event) => {
            setLoading(true);
            setPage(0);
            setSort(event.target.value as typeof sort);
          }}
          className="rounded-xl border border-white/10 bg-[#0e1622] px-3 py-2.5 text-sm"
        >
          <option value="name">По названию</option>
          <option value="price">По цене</option>
          <option value="performance">По производительности</option>
          <option value="newest">Сначала новые</option>
        </select>
        <label className="flex items-center gap-2 whitespace-nowrap rounded-xl border border-white/10 px-3 text-sm text-zinc-300">
          <input
            type="checkbox"
            checked={inStock}
            onChange={(event) => {
              setLoading(true);
              setPage(0);
              setInStock(event.target.checked);
            }}
          />
          Только с ценой
        </label>
      </section>

      {error && <p className="mb-4 rounded-xl bg-red-500/10 p-4 text-red-300">{error}</p>}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="shimmer h-56 rounded-2xl" />
          <div className="shimmer h-56 rounded-2xl" />
          <div className="shimmer h-56 rounded-2xl" />
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {products.map((product) => {
            const offers = [...product.offers]
              .filter((offer) => offer.in_stock)
              .sort((a, b) => Number(a.effective_price) - Number(b.effective_price));
            const cheapest = offers[0];
            const metadata = cheapest?.source_metadata ?? {};
            const isSnapshot = Boolean(metadata.snapshot);
            const observedAt =
              typeof metadata.observed_at === "string" ? metadata.observed_at : cheapest?.fetched_at;
            const comparing = compareIds.includes(product.id);

            return (
              <article key={product.id} className="glass-card flex min-h-80 flex-col overflow-hidden">
                <div className="relative flex h-48 items-center justify-center bg-gradient-to-br from-white to-slate-200 p-4">
                  <img
                    src={product.image_url || "/product-fallback.svg"}
                    alt={product.name}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    className="h-full w-full object-contain mix-blend-multiply"
                    onError={(event) => {
                      event.currentTarget.src = "/product-fallback.svg";
                    }}
                  />
                  <span className="absolute left-3 top-3 rounded-full bg-slate-950/80 px-2 py-1 text-[10px] font-bold uppercase text-cyan-200">
                    {CATEGORY_NAMES[product.category] ?? product.category}
                  </span>
                  {isSnapshot && (
                    <span className="absolute right-3 top-3 rounded-full bg-amber-400 px-2 py-1 text-[10px] font-bold text-amber-950">
                      Снимок цены
                    </span>
                  )}
                </div>
                <div className="flex flex-1 flex-col p-5">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold leading-snug">{product.name}</h3>
                      <p className="mt-1 text-xs text-zinc-600">
                        {product.brand} · {product.sku}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      <button
                        aria-label="Добавить к сравнению"
                        title="Сравнить"
                        onClick={() => toggleCompare(product.id)}
                        className={`rounded-xl p-2 ${comparing ? "bg-violet-500/20 text-violet-300" : "bg-white/5 text-zinc-600"}`}
                      >
                        <GitCompareArrows className="h-4 w-4" />
                      </button>
                      <button
                        aria-label="Избранное"
                        onClick={() => void toggleFavorite(product)}
                        className={`rounded-xl p-2 ${favorites.has(product.id) ? "bg-pink-500/15 text-pink-400" : "bg-white/5 text-zinc-600"}`}
                      >
                        <Heart
                          className="h-4 w-4"
                          fill={favorites.has(product.id) ? "currentColor" : "none"}
                        />
                      </button>
                    </div>
                  </div>
                  <div className="mb-4 flex flex-wrap gap-1.5">
                    {Object.entries(product.specs)
                      .filter(([key]) => key !== "catalog_source" && key !== "normalization_version")
                      .slice(0, 4)
                      .map(([key, value]) => (
                        <span
                          key={key}
                          title={key}
                          className="rounded-md bg-white/[0.04] px-2 py-1 text-[10px] text-zinc-400"
                        >
                          {key}: {displaySpec(value)}
                        </span>
                      ))}
                  </div>
                  <div className="mt-auto flex items-end justify-between gap-4">
                    <div>
                      {cheapest ? (
                        <>
                          <p className="text-xs text-zinc-500">{cheapest.store.name}</p>
                          <p className="text-xl font-bold text-cyan-300">
                            {Number(cheapest.effective_price).toLocaleString("pl-PL", {
                              minimumFractionDigits: 2,
                            })}{" "}
                            PLN
                          </p>
                          {observedAt && (
                            <p className="mt-1 text-[10px] text-zinc-600">
                              Цена от {new Date(observedAt).toLocaleString("ru-RU")}
                              {cheapest.stale ? " · требует обновления" : ""}
                            </p>
                          )}
                        </>
                      ) : (
                        <>
                          <p className="text-xs text-zinc-600">Каталожная карточка</p>
                          <p className="font-semibold text-zinc-500">Цена не импортирована</p>
                        </>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <button
                        title="История"
                        onClick={() => setHistoryProduct(product)}
                        className="rounded-lg bg-white/5 p-2 text-zinc-400 hover:text-cyan-300"
                      >
                        <History className="h-4 w-4" />
                      </button>
                      <button
                        title="Алерт цены"
                        onClick={() => void createAlert(product)}
                        className="rounded-lg bg-white/5 p-2 text-zinc-400 hover:text-amber-300"
                      >
                        <BellPlus className="h-4 w-4" />
                      </button>
                      {cheapest && (
                        <a
                          title="Открыть магазин"
                          target="_blank"
                          rel="noreferrer"
                          href={cheapest.url}
                          className="rounded-lg bg-white/5 p-2 text-zinc-400 hover:text-emerald-300"
                        >
                          <Store className="h-4 w-4" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <div className="mt-8 flex items-center justify-between">
        <p className="text-sm text-zinc-500">
          Показано {range} из {total.toLocaleString("ru-RU")}
        </p>
        <div className="flex items-center gap-3">
          <button
            disabled={page === 0}
            onClick={() => {
              setLoading(true);
              setPage((value) => value - 1);
            }}
            className="rounded-xl bg-white/5 p-2 disabled:opacity-30"
          >
            <ChevronLeft />
          </button>
          <span className="text-sm">
            {page + 1} / {pages}
          </span>
          <button
            disabled={page + 1 >= pages}
            onClick={() => {
              setLoading(true);
              setPage((value) => value + 1);
            }}
            className="rounded-xl bg-white/5 p-2 disabled:opacity-30"
          >
            <ChevronRight />
          </button>
        </div>
      </div>

      {compareIds.length > 0 && (
        <div className="fixed bottom-4 left-1/2 z-[60] w-[calc(100%-2rem)] max-w-4xl -translate-x-1/2 rounded-2xl border border-violet-400/20 bg-[#101522]/95 p-3 shadow-2xl backdrop-blur-xl">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-widest text-violet-400">
                Выбрано для сравнения: {compareIds.length}/{MAX_COMPARE}
              </p>
              <p className="mt-1 truncate text-sm text-zinc-400">
                {compareProducts.map((product) => product.name).join(" · ") || "Товары с другой страницы"}
              </p>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                onClick={() => setCompareIds([])}
                className="rounded-xl bg-white/5 px-4 py-2 text-sm text-zinc-400"
              >
                Очистить
              </button>
              <button
                disabled={compareIds.length < 2 || compareLoading}
                onClick={() => void runCompare()}
                className="rounded-xl bg-violet-500 px-5 py-2 text-sm font-bold disabled:opacity-40"
              >
                {compareLoading ? "Сравниваю..." : "Сравнить"}
              </button>
            </div>
          </div>
        </div>
      )}

      {historyProduct && (
        <ProductHistory product={historyProduct} onClose={() => setHistoryProduct(null)} />
      )}
      {compareResult && (
        <ProductComparison result={compareResult} onClose={() => setCompareResult(null)} />
      )}
    </main>
  );
}
