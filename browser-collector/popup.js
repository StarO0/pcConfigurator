let collected = null;

function pageCollector() {
  const first = (value) => Array.isArray(value) ? value[0] : value;
  const typed = (item, name) => Array.isArray(item?.["@type"])
    ? item["@type"].includes(name) : item?.["@type"] === name;
  const objects = [];
  document.querySelectorAll('script[type="application/ld+json"]').forEach((script) => {
    try {
      const parsed = JSON.parse(script.textContent.trim().replace(/;$/, ""));
      const list = Array.isArray(parsed) ? parsed : [parsed];
      list.forEach((entry) => {
        if (Array.isArray(entry?.["@graph"])) objects.push(...entry["@graph"]);
        else objects.push(entry);
      });
    } catch { /* malformed JSON-LD is ignored */ }
  });
  const product = objects.find((entry) => typed(entry, "Product")) || {};
  let offer = first(product.offers) || {};
  if (first(offer.offers)) offer = { ...offer, ...first(offer.offers) };
  const meta = (...names) => {
    for (const name of names) {
      const node = document.querySelector(`meta[property="${name}"],meta[name="${name}"]`);
      if (node?.content) return node.content.trim();
    }
    return null;
  };
  const text = (selector) => document.querySelector(selector)?.textContent?.trim() || null;
  const imageValue = first(product.image);
  const image = typeof imageValue === "object" ? imageValue.url || imageValue.contentUrl : imageValue;
  const brandValue = product.brand;
  const brand = typeof brandValue === "object" ? brandValue.name : brandValue;
  const specs = {};
  document.querySelectorAll("table tr, dl").forEach((row) => {
    const cells = row.querySelectorAll(":scope > th, :scope > td, :scope > dt, :scope > dd");
    if (cells.length >= 2) {
      const key = cells[0].textContent.replace(/\s+/g, " ").trim().replace(/:$/, "");
      const value = cells[1].textContent.replace(/\s+/g, " ").trim();
      if (key && value && key.length <= 120 && value.length <= 1000) specs[key] = value;
    }
  });
  const additional = Array.isArray(product.additionalProperty)
    ? product.additionalProperty : product.additionalProperty ? [product.additionalProperty] : [];
  additional.forEach((entry) => { if (entry?.name && entry?.value != null) specs[entry.name] = entry.value; });
  const rawPrice = offer.price || offer.lowPrice || meta("product:price:amount")
    || document.querySelector('[itemprop="price"]')?.getAttribute("content")
    || text('[itemprop="price"]');
  const name = product.name || meta("og:title", "twitter:title") || text("h1") || document.title;
  const sku = product.sku || document.querySelector('[itemprop="sku"]')?.getAttribute("content");
  const ean = product.gtin13 || product.gtin14 || product.gtin;
  const mpn = product.mpn;
  return {
    title: String(name || "").trim(), product_sku: sku ? String(sku) : null,
    ean: ean ? String(ean) : null, mpn: mpn ? String(mpn) : null,
    external_id: String(sku || ean || mpn || location.pathname), url: offer.url || location.href,
    price: rawPrice == null ? null : String(rawPrice), currency: offer.priceCurrency || meta("product:price:currency") || "PLN",
    in_stock: !/outofstock|soldout|unavailable/i.test(String(offer.availability || "")),
    brand: brand ? String(brand) : null, category: product.category ? String(product.category) : null,
    image_url: image || meta("og:image", "twitter:image"), specs,
    source_metadata: { source: "browser_collector", collected_at: new Date().toISOString() },
    page: { origin: location.origin, hostname: location.hostname }
  };
}

function slug(hostname) {
  return `${hostname.toLowerCase().replace(/^www\./, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}-browser`.slice(0, 80);
}

function categoryFrom(value, title, url) {
  const haystack = `${value || ""} ${title} ${url}`.toLowerCase();
  const rules = [
    ["motherboard", /motherboard|płyta główna|plyta glowna|mainboard/], ["gpu", /graphics|karta graficzna|radeon|geforce/],
    ["cpu", /processor|procesor|ryzen|core i[3579]/], ["ram", /memory|pamięć ram|pamiec ram|ddr[345]/],
    ["storage", /ssd|nvme|hard drive|dysk/], ["psu", /power supply|zasilacz/], ["case", /computer case|obudowa/],
    ["cooler", /cooler|cooling|chłodzenie|chlodzenie/], ["monitor", /monitor|display/], ["keyboard", /keyboard|klawiatura/],
    ["mouse", /mouse|mysz/], ["headphones", /headphone|headset|słuchawki|sluchawki/], ["webcam", /webcam|kamera internetowa/]
  ];
  return rules.find(([, pattern]) => pattern.test(haystack))?.[0] || null;
}

function price(value) {
  if (value == null || value === "") return null;
  const cleaned = String(value).replace(/\s/g, "").replace(/[^0-9,.-]/g, "");
  const normalized = cleaned.includes(",") && cleaned.includes(".")
    ? cleaned.replace(/\./g, "").replace(",", ".") : cleaned.replace(",", ".");
  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

document.getElementById("scan").addEventListener("click", async () => {
  const output = document.getElementById("result");
  output.className = "";
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: pageCollector });
    const selectedCategory = document.getElementById("category").value;
    const overridePrice = price(document.getElementById("price").value);
    const detectedCategory = categoryFrom(result.category, result.title, result.url);
    const item = {
      product_sku: result.product_sku, ean: result.ean, mpn: result.mpn, title: result.title,
      store_slug: slug(result.page.hostname), external_id: result.external_id, url: result.url,
      price: overridePrice || price(result.price), shipping_price: 0, currency: result.currency,
      in_stock: result.in_stock, brand: result.brand, category: selectedCategory || detectedCategory,
      image_url: result.image_url, specs: result.specs, source_metadata: result.source_metadata
    };
    collected = {
      source_slug: item.store_slug, source_name: `${result.page.hostname} — browser import`,
      source_base_url: result.page.origin, create_products: true, auto_accept: true,
      terms_confirmed: false, items: [item]
    };
    output.textContent = JSON.stringify(collected, null, 2);
    document.getElementById("save").disabled = false;
  } catch (error) {
    output.className = "error";
    output.textContent = `Не удалось прочитать страницу: ${error.message}`;
  }
});

document.getElementById("save").addEventListener("click", async () => {
  if (!collected) return;
  const encoded = encodeURIComponent(JSON.stringify(collected, null, 2));
  await chrome.downloads.download({
    url: `data:application/json;charset=utf-8,${encoded}`,
    filename: `pc-catalog-${collected.source_slug}-${Date.now()}.json`, saveAs: true
  });
});
