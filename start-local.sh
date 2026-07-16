#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
command -v docker >/dev/null || { echo "ERROR: Docker with Compose is required."; exit 1; }
docker info >/dev/null || { echo "ERROR: Docker daemon is not running."; exit 1; }
[[ -f .env ]] || cp .env.example .env
docker compose up --build -d
echo "Waiting for PostgreSQL, API and frontend..."
for _ in $(seq 1 80); do
  if curl -fsS "http://127.0.0.1:3000/api-backend/products?limit=1&in_stock=true" | grep -q '"total":[1-9]'; then
    echo "PC Configurator is ready: http://127.0.0.1:3000"
    exit 0
  fi
  sleep 3
done
echo "ERROR: services did not become ready. Run: docker compose logs api frontend db"
exit 1
