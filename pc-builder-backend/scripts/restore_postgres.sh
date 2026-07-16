#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 backups/file.dump" >&2
  exit 2
fi
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore --clean --if-exists -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "$1"
