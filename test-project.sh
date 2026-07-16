#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
command -v docker >/dev/null || { echo "ERROR: Docker with Compose is required."; exit 1; }
[[ -f .env ]] || cp .env.example .env

echo "[1/7] Build images (frontend lint + production build are part of the image build)"
docker compose build
echo "[2/7] Start PostgreSQL stack"
docker compose up -d
for _ in $(seq 1 80); do
  curl -fsS http://127.0.0.1:8000/api/v1/health/ready >/dev/null 2>&1 && break
  sleep 3
done
curl -fsS http://127.0.0.1:8000/api/v1/health/ready >/dev/null
echo "[3/7] PostgreSQL migration head"
docker compose exec -T api alembic current
echo "[4/7] Backend tests"
docker compose exec -T api python -m pytest -q
echo "[5/7] Ruff"
docker compose exec -T api python -m ruff check .
docker compose exec -T api python -m ruff format --check .
echo "[6/7] Live PostgreSQL/API smoke test"
docker compose exec -T api python scripts/smoke_test.py
echo "[7/7] Frontend-to-API proxy"
curl -fsS "http://127.0.0.1:3000/api-backend/products?limit=1&in_stock=true" | grep -q '"total":[1-9]'
echo "ALL TESTS PASSED"
