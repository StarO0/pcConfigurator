# PC Builder API v6.0

FastAPI backend backed by PostgreSQL 15, Redis and Celery. Runtime refuses non-PostgreSQL
`DATABASE_URL` outside the test environment.

Main data flow:

```text
Polish shop sitemap/feed
  -> JSON-LD/HTML extraction (price PLN, GTIN/MPN, stock)
  -> Open Icecat live lookup (identity, image, gallery, specs)
  -> complete-card quality gate
  -> product matching/deduplication
  -> PostgreSQL products + offers + price_history
```

Useful commands inside Docker:

```bash
docker compose exec api alembic current
docker compose exec api python -m app.scripts.seed
docker compose exec api python -m app.scripts.prune_incomplete_catalog
docker compose exec api python -m pytest -q
docker compose exec api python scripts/smoke_test.py
```

SQLite is used only by isolated unit-test fixtures. It is not a supported application runtime,
starter database or deployment mode.
