#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  attempt=1
  until alembic upgrade head; do
    if [ "$attempt" -ge 20 ]; then
      echo "Database migration failed after $attempt attempts" >&2
      exit 1
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
fi

if [ "${RUN_SEED:-false}" = "true" ]; then
  python -m app.scripts.seed
fi

exec "$@"
