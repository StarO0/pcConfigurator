import type { Build, BuildCategory, Component, ComponentCategory } from "@/data/builds";

// Keep browser requests on the frontend origin. Next.js proxies this path to FastAPI,
// so the UI does not depend on CORS, a second public port, or localhost resolution.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api-backend";

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  expires_at: string;
};

export type ApiUser = {
  id: string;
  email: string;
  display_name: string;
  role: "user" | "admin";
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
};

export type ApiOffer = {
  id: string;
  store: { id: string; slug: string; name: string; base_url: string; parser_type: string };
  url: string;
  price: string | number;
  shipping_price: string | number;
  effective_price: string | number;
  currency: string;
  in_stock: boolean;
  source_metadata: Record<string, unknown>;
  fetched_at: string;
  stale: boolean;
};

export type ApiProduct = {
  id: string;
  category: string;
  brand: string;
  name: string;
  sku: string;
  ean: string | null;
  mpn: string | null;
  specs: Record<string, unknown>;
  image_url: string | null;
  performance_score: number;
  quality_score: number;
  status: string;
  offers: ApiOffer[];
};

export type ApiProductCompare = {
  products: ApiProduct[];
  common_category: string | null;
  spec_keys: string[];
  lowest_effective_price_product_id: string | null;
  highest_performance_product_id: string | null;
};

export type ApiPage<T> = { items: T[]; total: number; limit: number; offset: number };

export type ApiPricePoint = {
  offer_id: string;
  store_name: string;
  currency: string;
  price: string | number;
  shipping_price: string | number;
  in_stock: boolean;
  recorded_at: string;
};

export type ApiPriceAlert = {
  id: string;
  product_id: string;
  target_price: string | number;
  currency: string;
  is_active: boolean;
  last_notified_price: string | number | null;
  created_at: string;
};

export type ApiNotification = {
  id: string;
  kind: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
};

export type ApiStore = {
  id: string;
  slug: string;
  name: string;
  base_url: string;
  country: string;
  is_active: boolean;
  parser_type: string;
  parser_config: Record<string, unknown>;
  last_success_at: string | null;
};

export type ApiHarvestDashboard = {
  records: number;
  accepted: number;
  pending: number;
  rejected: number;
  errors: number;
  queued_urls: number;
  products: number;
  products_with_images: number;
  image_coverage_percent: number;
  active_offers: number;
  snapshot_offers: number;
  source_count: number;
};

export type ApiHarvestRecord = {
  id: string;
  store_id: string;
  store_slug: string;
  product_id: string | null;
  source_url: string;
  external_id: string | null;
  status: string;
  title: string | null;
  brand: string | null;
  category: string | null;
  price: string | number | null;
  currency: string | null;
  image_url: string | null;
  match_confidence: number;
  match_method: string;
  quality_score: number;
  error_message: string | null;
  discovered_at: string;
  processed_at: string | null;
};

export type ApiEnrichmentStore = {
  id: string;
  slug: string;
  name: string;
  is_active: boolean;
  terms_confirmed: boolean;
  discovered_urls: number;
  crawl_offset: number;
  last_batch: Record<string, number>;
  last_discovery_batch: Record<string, number>;
  last_run_status: string | null;
  last_error_message: string | null;
  last_success_at: string | null;
  last_error_at: string | null;
};

export type ApiEnrichmentStatus = {
  products: number;
  products_with_images: number;
  products_with_offers: number;
  products_complete: number;
  products_with_multiple_stores: number;
  missing_images: number;
  missing_offers: number;
  coverage_percent: number;
  pending_ambiguous: number;
  stores: ApiEnrichmentStore[];
};

export type ApiHarvestImport = {
  received: number;
  accepted: number;
  pending: number;
  rejected: number;
  products_created: number;
  products_updated: number;
  offers_created: number;
  offers_updated: number;
  duplicates: number;
  errors: string[];
};

export type ApiParserRun = {
  id: string;
  store_id: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  error_count: number;
  error_message: string | null;
  metadata_json: Record<string, unknown>;
};

export type ApiDuplicateGroup = {
  key: string;
  reason: string;
  products: Array<Pick<ApiProduct, "id" | "category" | "brand" | "name" | "sku" | "ean" | "mpn">>;
};

export type ApiCompatibility = {
  status: "compatible" | "warning" | "incompatible";
  issues: Array<{
    code: string;
    severity: "error" | "warning" | "info";
    message: string;
    categories: string[];
    details: Record<string, string | number | boolean | null>;
  }>;
  estimated_peak_power_w: number;
  recommended_psu_w: number | null;
};

export type ApiBuild = {
  id: string;
  name: string;
  visibility: "private" | "unlisted" | "public";
  public_slug: string | null;
  profile: string;
  title: string;
  explanation: string;
  total_price: string | number;
  version: number;
  access_token?: string | null;
  compatibility_status: "compatible" | "warning" | "incompatible";
  bottleneck?: {
    status: "balanced" | "cpu_limited" | "gpu_limited";
    severity: "none" | "info" | "warning" | "critical";
    estimated_percent: number;
    message: string;
    recommended_products: Array<{ name: string }>;
  } | null;
  estimated_peak_power_w: number;
  components: Array<{
    category: string;
    product: ApiProduct;
    selected_offer: ApiOffer | null;
  }>;
};

type GenerateResponse = { builds: ApiBuild[] };

export type ApiPerformanceEstimate = {
  workload_slug: string;
  workload_name: string;
  kind: "game" | "render" | "productivity";
  resolution: string | null;
  settings: string | null;
  value: number;
  unit: string;
  confidence: "low" | "medium" | "high";
  disclaimer: string;
};

export type ApiBuildAnalysis = {
  build_id: string;
  performance: ApiPerformanceEstimate[];
  estimated_peak_power_w: number;
  recommended_psu_w: number;
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function detailMessage(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "API request failed";
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  return detail ? JSON.stringify(detail) : "API request failed";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  accessToken?: string | null,
  buildToken?: string | null,
  timeoutMs = 30_000,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (buildToken) headers.set("X-Build-Token", buildToken);
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  const abort = () => controller.abort();
  options.signal?.addEventListener("abort", abort, { once: true });
  try {
    const response = await fetch(`${API_URL}${path}`, { ...options, headers, signal: controller.signal });
    const payload = await response.json().catch(() => null);
    if (!response.ok) throw new ApiError(response.status, detailMessage(payload));
    return payload as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(408, "Превышено время ожидания ответа backend");
    }
    if (error instanceof TypeError) {
      throw new ApiError(
        503,
        "Локальный API недоступен. Запустите START_WINDOWS_FIXED.cmd и проверьте CHECK_WINDOWS.cmd",
      );
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
    options.signal?.removeEventListener("abort", abort);
  }
}

const CATEGORY_MAP: Record<string, ComponentCategory> = {
  cpu: "cpu",
  gpu: "gpu",
  ram: "ram",
  storage: "ssd",
  motherboard: "motherboard",
  psu: "psu",
  case: "case",
  cooler: "cooler",
};

const PROFILE_MAP: Record<string, BuildCategory> = {
  optimal: "optimal",
  economy: "economy",
  upgrade_ready: "futureproof",
  amd: "amd",
  intel_nvidia: "intel_nvidia",
};

const BADGES: Record<BuildCategory, { color: string; label: Record<string, string> }> = {
  optimal: {
    color: "#22c55e",
    label: { en: "Optimal", ru: "Оптимальная", uk: "Оптимальна", pl: "Optymalna" },
  },
  economy: {
    color: "#eab308",
    label: { en: "Economy", ru: "Экономная", uk: "Економна", pl: "Ekonomiczna" },
  },
  futureproof: {
    color: "#8b5cf6",
    label: { en: "Upgrade ready", ru: "Под апгрейд", uk: "Під апгрейд", pl: "Pod rozbudowę" },
  },
  amd: {
    color: "#ef4444",
    label: { en: "AMD", ru: "AMD", uk: "AMD", pl: "AMD" },
  },
  intel_nvidia: {
    color: "#06b6d4",
    label: { en: "Intel + NVIDIA", ru: "Intel + NVIDIA", uk: "Intel + NVIDIA", pl: "Intel + NVIDIA" },
  },
};

function value(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value ?? "—");
}

export function mapComponent(category: ComponentCategory, product: ApiProduct, selected: ApiOffer | null): Component {
  const offers = product.offers.filter((offer) => offer.in_stock && offer.currency === "PLN");
  const chosen = selected ?? offers[0] ?? null;
  const price = Number(chosen?.effective_price ?? chosen?.price ?? 0);
  const power = Number(product.specs.peak_power_w ?? product.specs.power_w ?? 0);
  return {
    id: product.id,
    category,
    name: product.name,
    price,
    image: product.image_url ?? undefined,
    specs: Object.fromEntries(Object.entries(product.specs).slice(0, 8).map(([key, item]) => [key, value(item)])),
    wattage: Number.isFinite(power) ? power : 0,
    shopLinks: offers.map((offer) => ({
      shop: offer.store.name,
      url: offer.url,
      price: Number(offer.effective_price ?? offer.price),
    })),
  };
}

export function mapApiBuild(item: ApiBuild): Build {
  const category = PROFILE_MAP[item.profile] ?? "optimal";
  const components = {} as Build["components"];
  for (const row of item.components) {
    const mappedCategory = CATEGORY_MAP[row.category];
    if (mappedCategory) components[mappedCategory] = mapComponent(mappedCategory, row.product, row.selected_offer);
  }
  const explanation = item.explanation || "Сборка рассчитана детерминированным движком совместимости.";
  return {
    id: item.id,
    backendId: item.id,
    accessToken: item.access_token ?? undefined,
    version: item.version,
    name: item.name,
    visibility: item.visibility,
    publicSlug: item.public_slug ?? undefined,
    compatibilityStatus: item.compatibility_status,
    bottleneck: item.bottleneck
      ? {
          status: item.bottleneck.status,
          severity: item.bottleneck.severity,
          estimatedPercent: item.bottleneck.estimated_percent,
          message: item.bottleneck.message,
          recommendedProduct: item.bottleneck.recommended_products[0]?.name,
        }
      : undefined,
    category,
    components,
    totalPrice: Number(item.total_price),
    aiExplanation: { en: explanation, ru: explanation, uk: explanation, pl: explanation },
    badge: item.profile === "manual"
      ? {
          color: "#06b6d4",
          label: { en: "Custom", ru: "Своя сборка", uk: "Власна збірка", pl: "Własny zestaw" },
        }
      : BADGES[category],
  };
}

export const api = {
  register: (email: string, displayName: string, password: string) =>
    request<TokenPair>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, display_name: displayName, password }),
    }),
  login: (email: string, password: string) =>
    request<TokenPair>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  refresh: (refreshToken: string) =>
    request<TokenPair>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
  me: (token: string) => request<ApiUser>("/auth/me", {}, token),
  logout: (token: string, refreshToken: string) =>
    request<{ message: string }>(
      "/auth/logout",
      { method: "POST", body: JSON.stringify({ refresh_token: refreshToken, all_sessions: false }) },
      token,
    ),
  generate: async (prompt: string, language: string, token?: string | null) => {
    const response = await request<GenerateResponse>(
      "/builds/generate",
      { method: "POST", body: JSON.stringify({ prompt, language, basket_mode: "balanced" }) },
      token,
      null,
      90_000,
    );
    return response.builds.map(mapApiBuild);
  },
  compatibility: (components: Record<string, string>, language: string) =>
    request<ApiCompatibility>("/catalog/compatibility", {
      method: "POST",
      body: JSON.stringify({ components, language }),
    }),
  createManualBuild: async (
    components: Record<string, string>,
    name: string,
    language: string,
    token: string,
  ) =>
    mapApiBuild(
      await request<ApiBuild>(
        "/builds/manual",
        {
          method: "POST",
          body: JSON.stringify({ name, components, language, currency: "PLN", basket_mode: "balanced" }),
        },
        token,
      ),
    ),
  saveBuild: async (build: Build, token: string) => {
    const response = await request<ApiBuild>(
      `/builds/${build.backendId ?? build.id}/save`,
      { method: "POST" },
      token,
      build.accessToken,
    );
    return mapApiBuild(response);
  },
  savedBuilds: async (token: string) => {
    const response = await request<ApiBuild[]>("/builds/saved/me/list", {}, token);
    return response.map(mapApiBuild);
  },
  publicBuild: async (slug: string) => mapApiBuild(await request<ApiBuild>(`/builds/public/${encodeURIComponent(slug)}`)),
  deleteBuild: (buildId: string, token: string) =>
    request<{ message: string }>(`/builds/${buildId}`, { method: "DELETE" }, token),
  updateBuild: async (
    build: Build,
    values: { name?: string; visibility?: "private" | "unlisted" | "public" },
    token: string,
  ) =>
    mapApiBuild(
      await request<ApiBuild>(
        `/builds/${build.backendId ?? build.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({ expected_version: build.version ?? 1, ...values }),
        },
        token,
        build.accessToken,
      ),
    ),
  exportBuild: (build: Build, token?: string | null) =>
    request<Record<string, unknown>>(
      `/builds/${build.backendId ?? build.id}/export`,
      {},
      token,
      build.accessToken,
    ),
  compareBuilds: (
    left: Build,
    right: Build,
    token?: string | null,
  ) =>
    request<{
      total_price_delta: string | number;
      delivery_price_delta: string | number;
      store_count_delta: number;
      differences: Array<{
        category: string;
        left_name: string | null;
        left_price: string | number | null;
        right_name: string | null;
        right_price: string | number | null;
        same_product: boolean;
      }>;
    }>(
      "/builds/compare",
      {
        method: "POST",
        body: JSON.stringify({
          left_id: left.backendId ?? left.id,
          right_id: right.backendId ?? right.id,
          left_token: left.accessToken,
          right_token: right.accessToken,
        }),
      },
      token,
    ),
  products: (params: {
    search?: string;
    category?: string;
    brand?: string;
    inStock?: boolean;
    sort?: "name" | "price" | "performance" | "newest";
    limit?: number;
    offset?: number;
  }) => {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.category) query.set("category", params.category);
    if (params.brand) query.append("brand", params.brand);
    query.set("in_stock", String(params.inStock ?? false));
    query.set("sort", params.sort ?? "name");
    query.set("limit", String(params.limit ?? 48));
    query.set("offset", String(params.offset ?? 0));
    return request<ApiPage<ApiProduct>>(`/products?${query}`);
  },
  productCategories: () => request<string[]>("/products/categories"),
  productBrands: (category?: string) =>
    request<string[]>(`/products/brands${category ? `?category=${encodeURIComponent(category)}` : ""}`),
  compareProducts: (productIds: string[]) =>
    request<ApiProductCompare>("/products/compare", {
      method: "POST",
      body: JSON.stringify({ product_ids: productIds }),
    }),
  favoriteProducts: (token: string) => request<ApiPage<ApiProduct>>("/products/favorites/me", {}, token),
  setFavorite: (productId: string, favorite: boolean, token: string) =>
    request<{ product_id: string; favorite: boolean }>(
      `/products/${productId}/favorite`,
      { method: favorite ? "POST" : "DELETE" },
      token,
    ),
  productPriceHistory: (productId: string, days = 90) =>
    request<{ product_id: string; points: ApiPricePoint[] }>(
      `/products/${productId}/price-history?days=${days}`,
    ),
  priceAlerts: (token: string) => request<ApiPriceAlert[]>("/price-alerts", {}, token),
  createPriceAlert: (productId: string, targetPrice: number, token: string) =>
    request<ApiPriceAlert>(
      "/price-alerts",
      { method: "POST", body: JSON.stringify({ product_id: productId, target_price: targetPrice, currency: "PLN" }) },
      token,
    ),
  deletePriceAlert: (alertId: string, token: string) =>
    request<{ message: string }>(`/price-alerts/${alertId}`, { method: "DELETE" }, token),
  notifications: (token: string) => request<ApiPage<ApiNotification>>("/notifications", {}, token),
  readNotification: (notificationId: string, token: string) =>
    request<ApiNotification>(`/notifications/${notificationId}/read`, { method: "POST" }, token),
  admin: {
    stats: (token: string) => request<Record<string, number>>("/admin/stats", {}, token),
    stores: (token: string) => request<ApiStore[]>("/admin/stores", {}, token),
    createStore: (
      values: { slug: string; name: string; base_url: string; parser_type: string; parser_config: Record<string, unknown> },
      token: string,
    ) => request<ApiStore>("/admin/stores", { method: "POST", body: JSON.stringify(values) }, token),
    updateStore: (storeId: string, values: Record<string, unknown>, token: string) =>
      request<ApiStore>(`/admin/stores/${storeId}`, { method: "PATCH", body: JSON.stringify(values) }, token),
    syncStore: (storeId: string, token: string) =>
      request<ApiParserRun>(`/admin/stores/${storeId}/sync-now`, { method: "POST" }, token, null, 180_000),
    parserRuns: (token: string) => request<ApiPage<ApiParserRun>>("/admin/parser-runs?limit=25", {}, token),
    harvesterDashboard: (token: string) =>
      request<ApiHarvestDashboard>("/admin/harvester/dashboard", {}, token),
    enrichmentStatus: (token: string) =>
      request<ApiEnrichmentStatus>("/admin/harvester/enrichment/status", {}, token),
    runEnrichment: (storeId: string, pages: number, termsConfirmed: boolean, token: string) =>
      request<ApiParserRun>(
        `/admin/harvester/enrichment/run/${storeId}`,
        {
          method: "POST",
          body: JSON.stringify({ pages, terms_confirmed: termsConfirmed }),
        },
        token,
        null,
        300_000,
      ),
    harvestRecords: (token: string, status = "pending") =>
      request<ApiPage<ApiHarvestRecord>>(
        `/admin/harvester/records?status=${encodeURIComponent(status)}&limit=100`,
        {},
        token,
      ),
    browserImport: (payload: Record<string, unknown>, token: string) =>
      request<ApiHarvestImport>(
        "/admin/harvester/browser-import",
        { method: "POST", body: JSON.stringify(payload) },
        token,
        null,
        180_000,
      ),
    extractHtml: (payload: Record<string, unknown>, token: string) =>
      request<Record<string, unknown>>(
        "/admin/harvester/extract-preview",
        { method: "POST", body: JSON.stringify(payload) },
        token,
      ),
    importHtml: (payload: Record<string, unknown>, token: string) =>
      request<ApiHarvestImport>(
        "/admin/harvester/html-import",
        { method: "POST", body: JSON.stringify(payload) },
        token,
        null,
        180_000,
      ),
    approveHarvest: (recordId: string, token: string) =>
      request<ApiHarvestImport>(
        `/admin/harvester/records/${recordId}/approve`,
        { method: "POST" },
        token,
      ),
    rejectHarvest: (recordId: string, token: string) =>
      request<{ message: string }>(
        `/admin/harvester/records/${recordId}/reject`,
        { method: "POST" },
        token,
      ),
    queueUrls: (storeSlug: string, urls: string[], token: string) =>
      request<{ message: string }>(
        "/admin/harvester/queue",
        { method: "POST", body: JSON.stringify({ store_slug: storeSlug, urls }) },
        token,
      ),
    processQueue: (storeId: string, token: string) =>
      request<{ message: string }>(
        `/admin/harvester/queue/process/${storeId}`,
        { method: "POST" },
        token,
        null,
        180_000,
      ),
    runDue: (token: string) =>
      request<{ checked: number; started: number; skipped: number; runs: string[] }>(
        "/admin/harvester/run-due",
        { method: "POST" },
        token,
        null,
        180_000,
      ),
    duplicates: (token: string) => request<ApiDuplicateGroup[]>("/admin/product-tools/duplicates", {}, token),
    merge: (source: string, target: string, token: string) =>
      request<{ message: string }>(
        "/admin/product-tools/merge",
        { method: "POST", body: JSON.stringify({ source_product_id: source, target_product_id: target }) },
        token,
      ),
    normalize: (token: string, dryRun = false) =>
      request<{ scanned: number; changed: number; dry_run: boolean }>(
        `/admin/product-tools/normalize?dry_run=${dryRun}`,
        { method: "POST" },
        token,
        null,
        180_000,
      ),
    importOffers: (offers: Array<Record<string, unknown>>, createProducts: boolean, token: string) =>
      request<{ created: number; updated: number; skipped: number; unmatched: Array<Record<string, unknown>> }>(
        "/admin/offers/import",
        { method: "POST", body: JSON.stringify({ offers, create_unmatched_products: createProducts }) },
        token,
        null,
        180_000,
      ),
    importProducts: (products: Array<Record<string, unknown>>, updateExisting: boolean, token: string) =>
      request<{ created: number; updated: number; skipped: number; errors: string[] }>(
        "/admin/product-tools/import",
        { method: "POST", body: JSON.stringify({ products, update_existing: updateExisting }) },
        token,
        null,
        180_000,
      ),
    previewFile: (file: File, token: string) => {
      const body = new FormData();
      body.set("file", file);
      return request<{ rows: Array<Record<string, unknown>>; total: number; truncated: boolean }>(
        "/admin/file-preview",
        { method: "POST", body },
        token,
        null,
        180_000,
      );
    },
    backup: async (token: string) => {
      const response = await fetch(`${API_URL}/admin/local-backup`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new ApiError(response.status, detailMessage(await response.json().catch(() => null)));
      return response.blob();
    },
    restore: (file: File, token: string) => {
      const body = new FormData();
      body.set("database", file);
      return request<{ message: string; restart_required: boolean }>(
        "/admin/local-restore",
        { method: "POST", body },
        token,
        null,
        180_000,
      );
    },
  },
  analysis: (build: Build, language: string, token?: string | null) =>
    request<ApiBuildAnalysis>(
      `/builds/${build.backendId ?? build.id}/analysis?language=${encodeURIComponent(language)}`,
      {},
      token,
      build.accessToken,
    ),
  replacementOptions: async (
    build: Build,
    category: ComponentCategory,
    accessToken?: string | null,
  ) => {
    const backendCategory = category === "ssd" ? "storage" : category;
    const response = await request<Array<{ product: ApiProduct; projected_total: string | number }>>(
      `/builds/${build.backendId ?? build.id}/replacement-options/${backendCategory}?sort=smart&limit=40`,
      {},
      accessToken,
      build.accessToken,
    );
    return response.map((item) => mapComponent(category, item.product, null));
  },
  replaceComponent: async (
    build: Build,
    category: ComponentCategory,
    component: Component,
    accessToken?: string | null,
  ) => {
    const backendCategory = category === "ssd" ? "storage" : category;
    const response = await request<ApiBuild>(
      `/builds/${build.backendId ?? build.id}/components/${backendCategory}`,
      {
        method: "PATCH",
        body: JSON.stringify({
          product_id: component.id,
          expected_version: build.version ?? 1,
          basket_mode: "balanced",
        }),
      },
      accessToken,
      build.accessToken,
    );
    const mapped = mapApiBuild(response);
    mapped.accessToken = build.accessToken;
    return mapped;
  },
};
