# Changelog

## 6.1.0 — production foundation hardening

- Fixed Docker frontend-to-API requests blocked by trusted-host validation.
- Removed the production build dependency on Google Fonts.
- Added frontend security headers and environment-based canonical site URL.
- Added safe XML catalogue/feed preview support with DOCTYPE/ENTITY rejection.
- Added API and UI comparison for two to four products.
- Fixed validation exceptions that could return HTTP 500 for custom Pydantic validators.
- Expanded backend coverage from 38 to 42 passing tests.
- Documented the exact starter snapshot limitations and final AI/data contracts.

## 6.0.0 — PostgreSQL ready-product catalogue

- removed the 67k metadata-only bootstrap and bundled SQLite database from the release;
- made PostgreSQL the only supported runtime database;
- added keyless Open Icecat GTIN/MPN enrichment with manufacturer images and galleries;
- added strict complete-card publishing and legacy incomplete-card pruning;
- converted Polish collectors from enrichment-only to ready-product acquisition;
- added product provenance fields and Alembic revision `77e6121a6d20`;
- replaced SQLite backup/restore with pg_dump/pg_restore custom archives;
- replaced fragile local Windows launchers with a Docker/PostgreSQL launcher.

## 5.2.0 — source-driven 67k catalog enrichment

- rotating product-sitemap/HTML-category enrichment for x-kom, Morele, Komputronik and RTV EURO AGD;
- corrected current Morele/RTV sitemap topology and added incremental Komputronik pagination discovery;
- 24-hour compressed URL cache and visible per-source failure diagnostics;
- coverage and per-source progress API plus an admin control panel;
- variant-safe matching using category, brand and normalized specifications;
- ambiguous products remain in staging and can no longer create accidental duplicates;
- local opt-in sources continue on the six-hour scheduler after the first confirmed batch;
- extraction fixes for Schema.org URLs, relative media links and mixed price locales.

## 5.1.1 — Windows API lifecycle fix

- frontend uses a same-origin `/api-backend` proxy for all browser requests;
- Windows launcher keeps API and frontend alive after its console closes;
- readiness now verifies health plus a real priced product through the proxy;
- added persistent logs, stack diagnostics, and a working local stop script.

## 5.1.0 — filled public snapshot

- 332 verified x-kom records across 16 PC-component and peripheral categories;
- 336 active snapshot offers in the bundled SQLite database;
- 310 distinct priced products, with an image attached to every active offer;
- starter snapshot provenance updated to 2026-07-15;
- backend/frontend versions and Russian launch documentation updated.

## 5.0.0 — keyless catalog harvester

### Added

- starter snapshot with 16 public-page observations, product photos, PLN prices and provenance;
- browser collector extension and admin upload UI;
- JSON-LD/Open Graph/CSS/HTML extraction plus XML/YML feed parsing;
- harvest staging records, URL queue, review workflow, quality dashboard and opt-in scheduler;
- keyless source configuration with stored terms confirmation, robots.txt, delay and retry limits;
- regression tests for cross-category and subset-name product collisions.

### Changed

- removed legacy fake `example.com` offers from the bundled SQLite database;
- fuzzy matching is bounded by category and brand and combines set/sorted token similarity;
- build generation gracefully returns available distinct profiles when a starter catalog is small;
- Windows launchers use ASCII wrappers and a validated PowerShell/Python startup path.

## 4.0.0 — autonomous data workspace

### Added

- full 66,814-product catalog UI contract and combined product price history;
- CSV/XLSX/JSON preview and bulk product import;
- normalization v2, duplicate discovery/merge and multilingual spec aliases;
- server-side manual builds using catalog products and compatibility validation;
- synchronous local store sync plus JSON-LD/sitemap keyless ingestion controls;
- local SQLite backup and validated deferred restore;
- compare/public/export, favorites, alerts and notification frontend contracts;
- desktop/mobile Playwright suite.

### Changed

- all bundled product specifications are normalized to version 2;
- sparse catalog fields no longer create false incompatibility errors;
- local normalization commits in safe bounded batches;
- browser-side vulnerable spreadsheet parser was replaced by local `openpyxl` parsing.

## 2.0.0 — product intelligence release

### Added

- multilingual request detection and localized responses for UK, EN, PL and RU;
- five business profiles: optimal, economy, upgrade-ready, AMD and Intel+NVIDIA;
- CPU/GPU bottleneck assessment in every build response;
- workload catalog and benchmark import API;
- FPS, render-time and productivity estimates with confidence/disclaimer;
- compatible bottleneck upgrade recommendations;
- smart replacement groups for cheaper alternatives and reasonable upgrades;
- detailed physical-clearance conflicts with missing millimetres/slots;
- monitor, UPS, keyboard, mouse and headset upsell recommendations;
- Redis-cached build analysis keyed by build version and language;
- Next.js-oriented TypeScript API client;
- workload profile Alembic migration and demo benchmark seed data;
- performance-engine and frontend-integration documentation.

### Changed

- build profiles now match product requirements instead of generic random variations;
- AI explanations preserve the language of the original request;
- compatibility messages are localizable and carry structured dimensions/details;
- replacement options default to smart product ranking;
- API version raised to 2.0.0.

### Notes

Demo benchmark values and store links are synthetic. Commercial deployment requires licensed benchmark data and authorized store feeds or affiliate APIs.
