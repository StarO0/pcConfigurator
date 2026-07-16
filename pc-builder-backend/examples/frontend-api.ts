const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type Language = "uk" | "en" | "pl" | "ru";
export type BuildProfile =
  | "optimal"
  | "economy"
  | "upgrade_ready"
  | "amd"
  | "intel_nvidia";

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_at: string;
};

export type Store = {
  id: string;
  slug: string;
  name: string;
  base_url: string;
  country: string;
  is_active: boolean;
};

export type Offer = {
  id: string;
  store: Store;
  external_id: string;
  url: string;
  price: string;
  shipping_price: string;
  effective_price: string;
  currency: string;
  in_stock: boolean;
  stock_quantity: number | null;
  fetched_at: string;
  stale: boolean;
};

export type Product = {
  id: string;
  category: string;
  brand: string;
  name: string;
  sku: string;
  ean: string | null;
  mpn: string | null;
  image_url: string | null;
  performance_score: number;
  noise_score: number;
  upgrade_score: number;
  quality_score: number;
  specs: Record<string, unknown>;
  version: number;
  offers: Offer[];
};

export type CompatibilityIssue = {
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
  categories: string[];
  details: Record<string, string | number | boolean | null>;
};

export type Bottleneck = {
  status: "balanced" | "cpu_limited" | "gpu_limited";
  severity: "none" | "info" | "warning" | "critical";
  limiting_component: "cpu" | "gpu" | null;
  estimated_percent: number;
  resolution: string;
  cpu_score: number;
  gpu_score: number;
  message: string;
  recommended_products: Product[];
};

export type Build = {
  id: string;
  profile: BuildProfile;
  title: string;
  name: string;
  prompt: string;
  explanation: string;
  requirements: {
    budget: number;
    currency: string;
    purposes: string[];
    resolution: "1080p" | "1440p" | "4k" | "8k" | null;
    target_fps: number | null;
    language: Language;
    [key: string]: unknown;
  };
  budget: string;
  currency: string;
  component_price: string;
  delivery_price: string;
  total_price: string;
  store_count: number;
  is_saved: boolean;
  visibility: "private" | "unlisted" | "public";
  public_slug: string | null;
  version: number;
  compatibility_status: "compatible" | "warning" | "incompatible";
  compatibility_issues: CompatibilityIssue[];
  bottleneck: Bottleneck;
  estimated_peak_power_w: number;
  recommended_psu_w: number;
  components: Array<{
    category: string;
    product: Product;
    selected_offer: Offer | null;
    quantity: number;
  }>;
};

export type GeneratedBuild = Build & { access_token: string | null };

export type ReplacementOption = {
  product: Product;
  is_compatible: boolean;
  issues: CompatibilityIssue[];
  projected_total: string;
  price_delta: string;
  performance_delta_percent: number;
  recommendation_group:
    | "cheaper_alternative"
    | "smart_upgrade"
    | "balanced"
    | "other";
  recommendation_reason: string;
  value_score: number;
};

export type PerformanceEstimate = {
  workload_slug: string;
  workload_name: string;
  kind: "game" | "render" | "productivity";
  resolution: string | null;
  settings: string | null;
  value: number;
  unit: string;
  confidence: "low" | "medium" | "high";
  limiting_component: "cpu" | "gpu" | "ram" | "balanced" | null;
  source: string | null;
  disclaimer: string;
};

export type BuildAnalysis = {
  build_id: string;
  bottleneck: Bottleneck;
  performance: PerformanceEstimate[];
  upsell: Array<{
    category: "monitor" | "ups" | "keyboard" | "mouse" | "headset";
    product: Product;
    reason: string;
    priority: number;
    projected_price: string | null;
  }>;
  estimated_peak_power_w: number;
  recommended_psu_w: number;
};

type RequestOptions = RequestInit & {
  buildToken?: string;
  retryAuth?: boolean;
};

const canUseStorage = () => typeof window !== "undefined";

const storage = {
  access: () => (canUseStorage() ? localStorage.getItem("access_token") : null),
  refresh: () => (canUseStorage() ? localStorage.getItem("refresh_token") : null),
  save(pair: TokenPair) {
    if (!canUseStorage()) return;
    localStorage.setItem("access_token", pair.access_token);
    localStorage.setItem("refresh_token", pair.refresh_token);
  },
  clear() {
    if (!canUseStorage()) return;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
  saveBuildToken(buildId: string, token: string | null) {
    if (canUseStorage() && token) localStorage.setItem(`build_token:${buildId}`, token);
  },
  buildToken: (buildId: string) =>
    canUseStorage() ? localStorage.getItem(`build_token:${buildId}`) : null,
};

async function refreshTokens(): Promise<boolean> {
  const refreshToken = storage.refresh();
  if (!refreshToken) return false;
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  if (!response.ok) {
    storage.clear();
    return false;
  }
  storage.save((await response.json()) as TokenPair);
  return true;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { buildToken, retryAuth = true, ...fetchOptions } = options;
  const token = storage.access();
  const response = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    cache: fetchOptions.cache ?? "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(buildToken ? { "X-Build-Token": buildToken } : {}),
      ...fetchOptions.headers,
    },
  });

  if (response.status === 401 && retryAuth && (await refreshTokens())) {
    return request<T>(path, { ...options, retryAuth: false });
  }
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown API error" }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : JSON.stringify(error.detail),
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const pcBuilderApi = {
  async generateBuilds(
    prompt: string,
    options: {
      budget?: number;
      currency?: string;
      language?: Language;
      basketMode?: "cheapest" | "fewest_stores" | "balanced";
    } = {},
  ) {
    const result = await request<{
      requirements: Build["requirements"];
      builds: GeneratedBuild[];
      cached: boolean;
    }>("/builds/generate", {
      method: "POST",
      body: JSON.stringify({
        prompt,
        budget: options.budget,
        currency: options.currency,
        language: options.language,
        basket_mode: options.basketMode ?? "balanced",
      }),
    });
    result.builds.forEach((build) =>
      storage.saveBuildToken(build.id, build.access_token),
    );
    return result;
  },

  getBuild(buildId: string) {
    return request<Build>(`/builds/${buildId}`, {
      buildToken: storage.buildToken(buildId) ?? undefined,
    });
  },

  getAnalysis(buildId: string, language?: Language, refresh = false) {
    const params = new URLSearchParams();
    if (language) params.set("language", language);
    if (refresh) params.set("refresh", "true");
    const query = params.size ? `?${params.toString()}` : "";
    return request<BuildAnalysis>(`/builds/${buildId}/analysis${query}`, {
      buildToken: storage.buildToken(buildId) ?? undefined,
    });
  },

  getReplacementOptions(
    buildId: string,
    category: string,
    options: {
      compatibleOnly?: boolean;
      brands?: string[];
      sort?: "smart" | "price" | "performance" | "noise" | "upgrade";
    } = {},
  ) {
    const params = new URLSearchParams({
      compatible_only: String(options.compatibleOnly ?? true),
      sort: options.sort ?? "smart",
    });
    options.brands?.forEach((brand) => params.append("brand", brand));
    return request<ReplacementOption[]>(
      `/builds/${buildId}/replacement-options/${category}?${params.toString()}`,
      { buildToken: storage.buildToken(buildId) ?? undefined },
    );
  },

  replaceComponent(build: Build, category: string, productId: string) {
    return request<Build>(`/builds/${build.id}/components/${category}`, {
      method: "PATCH",
      buildToken: storage.buildToken(build.id) ?? undefined,
      body: JSON.stringify({
        product_id: productId,
        expected_version: build.version,
        basket_mode: "balanced",
      }),
    });
  },

  getWorkloads(language: Language, kind?: "game" | "render" | "productivity") {
    const params = new URLSearchParams({ language });
    if (kind) params.set("kind", kind);
    return request<
      Array<{
        slug: string;
        name: string;
        names: Record<Language, string>;
        kind: "game" | "render" | "productivity";
        unit: string;
        lower_is_better: boolean;
        accelerator: "cpu" | "gpu" | "hybrid";
        default_resolution: string | null;
        settings: string | null;
        source_url: string | null;
      }>
    >(`/benchmarks/workloads?${params.toString()}`);
  },

  compare(left: GeneratedBuild, right: GeneratedBuild) {
    return request<{
      left: Build;
      right: Build;
      differences: unknown[];
      total_price_delta: string;
    }>("/builds/compare", {
      method: "POST",
      body: JSON.stringify({
        left_id: left.id,
        right_id: right.id,
        left_token: left.access_token ?? storage.buildToken(left.id),
        right_token: right.access_token ?? storage.buildToken(right.id),
      }),
    });
  },

  register(email: string, displayName: string, password: string) {
    return request<TokenPair>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        display_name: displayName,
        password,
      }),
    }).then((pair) => (storage.save(pair), pair));
  },

  login(email: string, password: string) {
    return request<TokenPair>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }).then((pair) => (storage.save(pair), pair));
  },

  async logout(allSessions = false) {
    await request("/auth/logout", {
      method: "POST",
      body: JSON.stringify({
        refresh_token: storage.refresh(),
        all_sessions: allSessions,
      }),
    });
    storage.clear();
  },

  saveBuild(buildId: string) {
    return request<Build>(`/builds/${buildId}/save`, {
      method: "POST",
      buildToken: storage.buildToken(buildId) ?? undefined,
    });
  },

  getSavedBuilds() {
    return request<Build[]>("/builds/saved/me/list");
  },

  searchProducts(params: URLSearchParams) {
    return request<{
      items: Product[];
      total: number;
      limit: number;
      offset: number;
    }>(`/products?${params}`);
  },

  createPriceAlert(productId: string, targetPrice: number, currency = "PLN") {
    return request("/price-alerts", {
      method: "POST",
      body: JSON.stringify({
        product_id: productId,
        target_price: targetPrice,
        currency,
      }),
    });
  },
};
