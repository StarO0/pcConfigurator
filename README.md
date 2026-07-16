# PC Configurator — исправленный запуск

Для Windows: установите и запустите Docker Desktop, затем дважды нажмите **`START_PROJECT.bat`**. Подробности находятся в `ПРОСТОЙ_ЗАПУСК.md`.

# PC Configurator Unified v6.1

Production-oriented foundation for a Polish PC configurator. The application is already wired end to end: Next.js frontend, FastAPI API, PostgreSQL, Redis, Celery workers, Alembic migrations, authentication, builds, compatibility, catalogue management, prices, history, favourites, alerts, admin tools and automated tests.

The two intentionally unfinished product areas are:

1. a large normalized catalogue with reliable category-specific specifications and current Polish offers;
2. the final conversational AI experience and production model prompts.

## Quick start

Docker Desktop is the only required runtime dependency.

- Windows: run `start-windows.bat`.
- Linux/macOS: run `./start-local.sh`.
- Frontend: <http://localhost:3000>
- API documentation: <http://localhost:8000/docs>
- Stop: `stop-windows.bat` or `docker compose down`.

For local development `.env.example` creates this administrator:

- email: `admin@pcbuilder.app`
- password: `Local-admin-123`

Change all secrets before any public deployment.

## Implemented

| Area | Status |
|---|---|
| PostgreSQL 15 + Alembic | Primary runtime database, one linear migration head |
| Docker Compose | Frontend, API, PostgreSQL, Redis, Celery worker and Celery Beat |
| Catalogue API | Search, filters, categories, brands, sorting, pagination and product details |
| Import pipeline | JSON, CSV, XLSX/XLSM and safe flat XML preview/import mapping |
| Product matching | SKU, EAN/GTIN, MPN + brand and guarded fuzzy matching |
| Prices | Multiple stores, shipping, stock, stale state and best effective price |
| Price history | Per-offer and per-product history, 730-day retention |
| Users | Registration, login, refresh rotation, sessions, password reset and verification contracts |
| Builds | AI/rules generation, manual builds, save, clone, revisions, trash, restore, export and public links |
| Compatibility | Socket, RAM, case, GPU, cooler, storage, PSU and power checks |
| Comparison | Build comparison and 2–4 product comparison matrix in the catalogue |
| Favourites | Authenticated product favourites |
| Alerts | Target-price alerts, in-app notifications and optional SMTP email |
| Background jobs | Store sync every 6 hours, NBP rates, alerts and cleanup |
| Administration | Products, stores, imports, parser runs, users, audit log, backup/restore and harvester staging |
| Observability | Structured logs, request IDs, health endpoints, Prometheus metrics and optional Sentry |
| Frontend integration | Same-origin `/api-backend` proxy; no browser CORS or external-font dependency |
| AI contract | Swappable provider interface for rules/OpenAI/Gemini/DeepSeek with deterministic validation |

## Starter data: exact state

The included snapshot is deliberately small and is not the final catalogue:

- 332 products;
- 16 categories;
- 86 brands;
- 332 images;
- 332 PLN offers and source URLs;
- no EAN values in the bundled snapshot;
- no MPN values in the bundled snapshot;
- many snapshot products still need normalized technical specifications.

Therefore the snapshot is useful for catalogue, price, favourites, alerts, history, comparison and admin flows. A fully reliable configurator requires the remaining data task: import products with category-specific specs such as socket, RAM type, dimensions, capacity and power.

## Data model

```text
users ── auth_sessions / one_time_tokens / favourites / alerts / notifications
products ── offers ── price_history
products ── benchmarks
builds ── build_components ── products/offers
builds ── build_revisions
stores ── parser_runs / harvest_records / crawl_queue
service_tokens / audit_logs / ai_usage
```

## Tests

Without Docker:

```bash
cd pc-builder-backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q
.venv/bin/ruff check app tests migrations

cd ../front
npm ci
npm run lint
npm run build
```

Full Docker smoke test:

```bash
./test-project.sh
```

or on Windows:

```text
test-project-windows.bat
```

## Important production settings

Set strong values for `SECRET_KEY`, `TOKEN_PEPPER`, `POSTGRES_PASSWORD` and the administrator password. Set `ENVIRONMENT=production`, `AUTO_CREATE_TABLES=false`, exact `CORS_ORIGINS`, exact `TRUSTED_HOSTS`, `FRONTEND_URL`, SMTP/Sentry credentials when needed, and enable only data collectors whose terms and robots policy were reviewed.

See:

- `PROJECT_COMPLETION_STATUS.md`
- `pc-builder-backend/docs/AI_INTEGRATION_CONTRACT.md`
- `pc-builder-backend/docs/PARSER_ADAPTER.md`
- `ИНСТРУКЦИЯ_ЗАПУСКА.md`
